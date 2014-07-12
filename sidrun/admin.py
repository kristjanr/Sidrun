from django.contrib import admin

from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.contrib.admin.templatetags.admin_modify import *
from django.contrib.admin.templatetags.admin_modify import submit_row as original_submit_row
from django.contrib import messages
from sidrun import models

from sidrun.models import Tag, Type, ViewTasks, NewTasks, TaskForInternFullInfo, InternTask
from tasks.forms import AddTypeAndTagsForms


# or
# original_submit_row = submit_row

@register.inclusion_tag('admin/submit_line.html', takes_context=True)
def submit_row(context):
    ctx = original_submit_row(context)
    ctx.update({
        'show_save_and_add_another': context.get('show_save_and_add_another', ctx['show_save_and_add_another']),
        'show_save_and_continue': context.get('show_save_and_continue', ctx['show_save_and_continue']),
        'show_save': context.get('show_save', ctx['show_save']),
        'show_accept': context.get('show_accept')
    })
    return ctx


class TaskLessInfo(admin.ModelAdmin):
    list_display = ('title', 'type', 'type_icon', 'number_of_current_positions', 'start_date')
    readonly_fields = ['title', 'tags_list', 'type', 'type_icon', 'description', 'requirements', 'submission_type',
                       'start_date',
                       'finish_date', 'number_of_current_positions']
    fields = ['title', 'type', 'description', 'requirements', 'submission_type', 'start_date',
              'finish_date', 'number_of_current_positions']

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = {
            'show_save_and_add_another': False,
            'show_save_and_continue': False,
            'show_save': False,
            'show_accept': True
        }
        return super(TaskLessInfo, self).change_view(request, object_id,
                                                     form_url, extra_context=extra_context)

    def response_change(self, request, obj):
        """
        Determines the HttpResponse for the change_view stage.
        """
        opts = self.model._meta
        pk_value = obj._get_pk_val()
        preserved_filters = self.get_preserved_filters(request)

        if "_accept" in request.POST:
            user = request.user
            pending_tasks = user.interntask_set
            n_pending_tasks = pending_tasks.count()
            allowed_number_of_pending_tasks = user.profile.allowed_number_of_tasks
            msg = ''
            if allowed_number_of_pending_tasks <= n_pending_tasks:
                msg = _('You are allowed to have %d pending tasks. You have already have %d pending tasks!' % (
                allowed_number_of_pending_tasks, pending_tasks.count()))
            if pending_tasks.filter(task=obj):
                msg += _(' You already have this task!')
            if allowed_number_of_pending_tasks > n_pending_tasks and not pending_tasks.filter(task=obj):
                new_intern_task = pending_tasks.create(task=obj, user=user, status=models.InternTask.UNFINISHED)
                new_intern_task_pk = new_intern_task._get_pk_val()
                msg = _(
                    'Task %s was assigned to you. You now have %d pending task(s).' % (obj.title, pending_tasks.count()))
                redirect_url = reverse('admin:%s_%s_change' %
                                       (opts.app_label, 'interntask'),
                                       args=(new_intern_task_pk,),
                                       current_app=self.admin_site.name)
            else:
                redirect_url = request.path
            self.message_user(request, msg, messages.SUCCESS)
            redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
            return HttpResponseRedirect(redirect_url)


class TaskFullInfo(admin.ModelAdmin):
    readonly_fields = ['title', 'tags_list', 'type', 'type_icon', 'description', 'requirements', 'submission_type',
                       'start_date',
                       'finish_date', 'number_of_current_positions', 'expected_results', 'extra_material']
    fields = ['title', 'type', 'description', 'requirements', 'submission_type', 'start_date',
              'finish_date', 'number_of_current_positions', 'expected_results', 'extra_material']


class ForAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'type', 'tags_list', 'submission_type', 'application_deadline', 'start_date', 'finish_date',
        'number_of_positions',)
    form = AddTypeAndTagsForms


class AddTag(admin.ModelAdmin):
    list_display = ('name',)


class AddType(admin.ModelAdmin):
    list_display = ('name',)


class InternTaskEdit(admin.ModelAdmin):
    list_display = ('task_type', 'task_name', 'date_started', 'status', 'feedback')
    fields = ['summary_pitch', 'body', 'conclusion', 'references', 'video']

    def get_queryset(self, request):
        return super(InternTaskEdit, self).get_queryset(request).filter(user=request.user)

admin.site.register(InternTask, InternTaskEdit)
admin.site.register(TaskForInternFullInfo, TaskFullInfo)
admin.site.register(ViewTasks, TaskLessInfo)
admin.site.register(NewTasks, ForAdmin)
admin.site.register(Tag, AddTag)
admin.site.register(Type, AddType)