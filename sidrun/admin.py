from django.contrib import admin
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _
from django.contrib.admin.templatetags.admin_modify import *
from django.contrib.admin.templatetags.admin_modify import submit_row as original_submit_row
from django.contrib import messages

from sidrun import models
from sidrun.forms import CustomInlineFormSet
from sidrun.models import AdminTask, Task, Tag, Type, InternTask
from tasks.forms import AddTypeAndTagsForms


@register.inclusion_tag('admin/submit_line.html', takes_context=True)
def submit_row(context):
    ctx = original_submit_row(context)
    ctx.update({
        'show_save_and_add_another': context.get('show_save_and_add_another', ctx['show_save_and_add_another']),
        'show_save_and_continue': context.get('show_save_and_continue', ctx['show_save_and_continue']),
        'show_save': context.get('show_save', ctx['show_save']),
        'show_abandon': context.get('show_abandon'),
        'show_accept': context.get('show_accept'),
        'show_preview': context.get('show_preview'),
        'show_submit': context.get('show_submit'),
        'show_back': context.get('show_back')
    })
    return ctx


class InternTaskInline(admin.StackedInline):
    formset = CustomInlineFormSet
    model = InternTask
    fk_name = 'task'
    list_display = ('task_type', 'task_name', 'date_started', 'status', 'feedback')
    fields = ['summary_pitch', 'body', 'conclusion', 'references', 'video']
    extra = 0
    can_delete = True

    def get_formset(self, request, obj=None, **kwargs):
        modelformset = super(InternTaskInline, self).get_formset(request, obj, **kwargs)

        class ModelFormSetMetaClass(modelformset):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return modelformset(*args, **kwargs)
        return ModelFormSetMetaClass

    def get_queryset(self, request):
        return super(InternTaskInline, self).get_queryset(request).filter(user=request.user)

    def has_add_permission(self, request):
        return False

    def get_readonly_fields(self, request, obj=None):
        intern_tasks_of_user = obj.interntask_set.filter(user=request.user)
        user_has_accepted_task = bool(intern_tasks_of_user.count())
        if user_has_accepted_task:
            interntask_status = intern_tasks_of_user[0].status
            if (interntask_status == models.InternTask.ABANDONED
                or interntask_status == models.InternTask.FINISHED
                or request.GET.get('preview')):
                return self.readonly_fields + ('summary_pitch', 'body', 'conclusion', 'references', 'video')
        return self.readonly_fields


class TaskForIntern(admin.ModelAdmin):
    list_display = ('title', 'type', 'type_icon', 'number_of_current_positions', 'start_date')
    readonly_fields = ('title', 'tags_list', 'type', 'type_icon', 'description', 'requirements', 'submission_type',
                       'start_date', 'finish_date', 'expected_results', 'extra_material')
    fields = ['title', 'type', 'description', 'requirements', 'submission_type', 'start_date',
              'finish_date']

    def change_view(self, request, object_id, form_url='', extra_context=None):
        intern_tasks_of_user = request.user.interntask_set.filter(task_id=object_id)
        user_has_accepted_task = bool(intern_tasks_of_user.count())
        if user_has_accepted_task:
            interntask_status = intern_tasks_of_user[0].status
        else:
            interntask_status = None
        if interntask_status and interntask_status == models.InternTask.UNFINISHED or interntask_status == models.InternTask.UNSUBMITTED:
            is_preview = bool(request.GET.get('preview'))
            extra_context = {
                'show_save_and_add_another': False,
                'show_save': False,
                'show_save_and_continue': user_has_accepted_task and not is_preview,
                'show_abandon': user_has_accepted_task,
                'show_accept': not user_has_accepted_task,
                'show_preview': user_has_accepted_task and not is_preview,
                'show_submit': is_preview,
                'show_back': is_preview
            }
        else:
            extra_context = {
                'show_save_and_add_another': False,
                'show_save_and_continue': False,
                'show_save': False,
                'show_abandon': False,
                'show_accept': not user_has_accepted_task,
                'show_preview': False,
                'show_submit': False,
                'show_back': False
            }
        return super(TaskForIntern, self).change_view(request, object_id,
                                                      form_url, extra_context=extra_context)

    def response_change(self, request, obj):
        """
        Determines the HttpResponse for the change_view stage.
        """
        opts = self.model._meta
        pk_value = obj._get_pk_val()
        preserved_filters = self.get_preserved_filters(request)
        user = request.user
        if '_accept' in request.POST and not self.user_has_accepted_task(obj, user):
            pending_tasks = user.interntask_set
            n_pending_tasks = pending_tasks.count()
            allowed_number_of_pending_tasks = user.profile.allowed_number_of_tasks
            msg = ''
            if allowed_number_of_pending_tasks <= n_pending_tasks:
                msg = _('You are allowed to have %d pending tasks. You already have %d pending tasks! ' % (
                    allowed_number_of_pending_tasks, pending_tasks.count()))
            if pending_tasks.filter(task=obj):
                msg += _('You already have this task!')
            if allowed_number_of_pending_tasks > n_pending_tasks and not pending_tasks.filter(task=obj):
                new_intern_task = pending_tasks.create(task=obj, user=user, status=models.InternTask.UNFINISHED)
                new_intern_task_pk = new_intern_task._get_pk_val()
                msg = _(
                    'Task %s was assigned to you. You now have %d pending task(s).' % (
                        obj.title, pending_tasks.count()))
                redirect_url = reverse('admin:%s_%s_change' %
                                       (opts.app_label, 'task'),
                                       args=(pk_value,),
                                       current_app=self.admin_site.name)
                self.message_user(request, msg, messages.SUCCESS)

            else:
                self.message_user(request, msg, messages.WARNING)
                redirect_url = request.path
            redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
            return HttpResponseRedirect(redirect_url)

        elif '_abandon' in request.POST and self.user_has_accepted_task(obj, user):
            obj.interntask_set.filter(user=user).update(status=models.InternTask.ABANDONED)
            msg_dict = {'name': force_text(opts.verbose_name), 'obj': force_text(obj)}
            msg = _('The %(name)s "%(obj)s" was abandoned!') % msg_dict
            self.message_user(request, msg, messages.WARNING)
            return self.response_post_save_change(request, obj)
        elif '_preview' in request.POST and self.user_has_accepted_task(obj, user):
            redirect_url = request.path + '?preview=true'
            redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
            return HttpResponseRedirect(redirect_url)
        elif '_submit' in request.POST and self.user_has_accepted_task(obj, user):
            obj.interntask_set.filter(user=user).update(status=models.InternTask.FINISHED)
            msg_dict = {'name': force_text(opts.verbose_name), 'obj': force_text(obj)}
            msg = _('You submitted the %(name)s "%(obj)s"!') % msg_dict
            self.message_user(request, msg, messages.SUCCESS)
            return self.response_post_save_change(request, obj)
        else:
            return super(TaskForIntern, self).response_change(request, obj)

    @staticmethod
    def user_has_accepted_task(obj, user):
        intern_tasks_of_user = obj.interntask_set.filter(user=user)
        return bool(intern_tasks_of_user.count())

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(TaskForIntern, self).get_fieldsets(request, obj)
        if self.user_has_accepted_task(obj, request.user):
            fields_ = fieldsets[0][1]['fields']
            if 'extra_material' not in fields_ and 'expected_results' not in fields_:
                fields_.extend(['expected_results', 'extra_material'])
                self.inlines = [InternTaskInline]
        return fieldsets


class TaskForAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'type', 'tags_list', 'submission_type', 'application_deadline', 'start_date', 'finish_date',
        'number_of_positions',)
    form = AddTypeAndTagsForms


class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)


class TypeAdmin(admin.ModelAdmin):
    list_display = ('name',)


admin.site.register(AdminTask, TaskForAdmin)
admin.site.register(Task, TaskForIntern)
admin.site.register(Tag, TagAdmin)
admin.site.register(Type, TypeAdmin)