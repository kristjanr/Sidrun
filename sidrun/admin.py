from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db.models import TextField, Q, CharField
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _
from django.contrib.admin.templatetags.admin_modify import *
from django.contrib.admin.templatetags.admin_modify import submit_row as original_submit_row
from django.contrib import messages
from django_summernote.widgets import SummernoteWidget

from sidrun import models
from sidrun.forms import CustomForm, AddTaskForm
from sidrun.models import AdminTask, Task, Tag, Type, InternTask, HelpText, AdminHelpText


@register.inclusion_tag('admin/submit_line.html', takes_context=True)
def submit_row(context):
    ctx = original_submit_row(context)
    ctx.update({
        'show_save_and_continue': context.get('show_save_and_continue', ctx['show_save_and_continue']),
        'show_abandon': context.get('show_abandon'),
        'show_accept': context.get('show_accept'),
        'show_preview': context.get('show_preview'),
        'show_submit': context.get('show_submit'),
        'show_back': context.get('show_back'),
        'show_publish': context.get('show_publish')
    })
    return ctx


def calculate_time_left(obj):
    return obj.task.time_to_complete_task * 3600 - (timezone.now() - obj.time_started).seconds


def overtime(obj):
    if type(obj) == str or type(obj) == int:
        obj = InternTask.objects.get(id=obj)
    time_left = calculate_time_left(obj)
    return 0 > time_left


def show_interntask_as_readonly(obj, request):
    return (obj.status == models.InternTask.ABANDONED
            or obj.status == models.InternTask.FINISHED
            or request.GET.get('preview')
            or overtime(obj)
            or request.user.groups.filter(name='admins').exists())


def show_task_as_readonly(obj, request):
    if obj:
        return obj.start_date or request.GET.get('preview')
    else:
        return False


class ViewNewTasks(admin.ModelAdmin):
    list_display = ('title', 'type', 'type_icon', 'available_positions', 'deadline',
                    'time_to_complete_task')
    readonly_fields = ('title', 'tags_list', 'type', 'type_icon', 'description', 'requirements', 'submission_type',
                       'start_date', 'deadline', 'time_to_complete_task', 'number_of_positions', 'available_positions',)
    fields = ['title', 'description', 'requirements', 'submission_type', 'deadline', 'time_to_complete_task',
              'number_of_positions', 'available_positions']
    can_delete = False
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        queryset = super(ViewNewTasks, self).get_queryset(request)
        now = timezone.now()
        return queryset.exclude(interntask__user=request.user) \
            .filter(start_date__lte=now).\
            extra(where=["deadline > now() + interval '1 hour' * time_to_complete_task ",
                         "number_of_positions > (SELECT COUNT(*) FROM sidrun_interntask WHERE sidrun_interntask.task_id = sidrun_task.id AND status != 'AB')"])

    def change_view(self, request, object_id, form_url='', extra_context=None):
        intern_tasks_of_user = request.user.interntask_set.filter(task_id=object_id)
        user_has_accepted_task = bool(intern_tasks_of_user.count())
        if not user_has_accepted_task:
            extra_context = {
                'show_save_and_continue': False,
                'show_abandon': False,
                'show_accept': not user_has_accepted_task,
                'show_preview': False,
                'show_submit': False,
                'show_back': False,
            }
        return super(ViewNewTasks, self).change_view(request, object_id,
                                                     form_url, extra_context=extra_context)

    def get_n_pending_tasks(self, pending_tasks):
        counter = 0
        pending_tasks = pending_tasks.filter(Q(status=InternTask.UNFINISHED)).all()
        for task in pending_tasks:
            if not overtime(task):
                counter += 1
        return counter

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
            n_pending_tasks = self.get_n_pending_tasks(pending_tasks)
            allowed_number_of_pending_tasks = user.profile.allowed_number_of_tasks
            msg = ''
            if allowed_number_of_pending_tasks <= n_pending_tasks:
                msg = _('You are allowed to have %d pending tasks. You already have %d pending task(s)! ' % (
                    allowed_number_of_pending_tasks, n_pending_tasks))
                self.message_user(request, msg, messages.WARNING)
            if pending_tasks.filter(task=obj):
                msg += _('You already have this task!')
                self.message_user(request, msg, messages.WARNING)
            if allowed_number_of_pending_tasks > n_pending_tasks and not pending_tasks.filter(task=obj):
                new_intern_task = pending_tasks.create(task=obj, user=user, status=models.InternTask.UNFINISHED)
                new_intern_task_pk = new_intern_task._get_pk_val()
                n_pending_tasks = self.get_n_pending_tasks(pending_tasks)
                msg = _(
                    'Task %s was assigned to you. You now have %d pending task(s).' % (
                        obj.title, n_pending_tasks))
                redirect_url = reverse('admin:%s_%s_change' %
                                       (opts.app_label, 'interntask'),
                                       args=(new_intern_task_pk,),
                                       current_app=self.admin_site.name)
                self.message_user(request, msg, messages.SUCCESS)
                redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
                return HttpResponseRedirect(redirect_url)
            return self.response_post_save_change(request, obj)
        else:
            return super(ViewNewTasks, self).response_change(request, obj)

    @staticmethod
    def user_has_accepted_task(obj, user):
        intern_tasks_of_user = obj.interntask_set.filter(user=user)
        return bool(intern_tasks_of_user.count())


class AcceptedInterntasks(admin.TabularInline):
    model = InternTask
    fields = ['user', 'time_started', 'time_ended', 'status', 'overtime', 'link']
    readonly_fields = ('user', 'status', 'time_started', 'time_ended', 'overtime', 'link')

    def link(self, obj):
        if obj.status == InternTask.FINISHED or obj.status == InternTask.ABANDONED or overtime(obj):
            opts = self.model._meta
            interntask_url = reverse('admin:%s_%s_change' %
                                   (opts.app_label, 'interntask'),
                                   args=(obj.id,),
                                   current_app=self.admin_site.name)

            return '<a href="%s">%s</a>' % (interntask_url, obj.task.title)
        else:
            return obj.task.title

    link.allow_tags = True

    def overtime(self, obj):
        return overtime(obj)


class TaskForAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'type', 'tags_list', 'submission_type', 'time_to_complete_task', 'start_date', 'deadline',
        'number_of_positions', 'number_of_users_accepted')
    fields = ['title', 'type', 'tags', 'description', 'requirements', 'submission_type', 'time_to_complete_task',
                     'deadline', 'number_of_positions', 'expected_results', 'extra_material', 'require_references', 'require_videos']
    readonly_fields = ('start_date',)
    form = AddTaskForm
    inlines = [AcceptedInterntasks]
    formfield_overrides = {TextField: {'widget': SummernoteWidget()}, CharField: {'widget': SummernoteWidget()}}

    def number_of_users_accepted(self, obj):
        return obj.interntask_set.all().count()

    def get_form(self, request, obj=None, **kwargs):
        modelform = super(TaskForAdmin, self).get_form(request, obj, **kwargs)

        class ModelFormAdminMetaClass(modelform):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return modelform(*args, **kwargs)

        return ModelFormAdminMetaClass

    def get_readonly_fields(self, request, obj=None):
        if show_task_as_readonly(obj, request):
            return ('title', 'type', 'tags', 'description', 'requirements', 'submission_type', 'time_to_complete_task',
                    'start_date', 'deadline', 'number_of_positions', 'expected_results', 'extra_material', 'require_references', 'require_videos')
        return self.readonly_fields

    def change_view(self, request, object_id, form_url='', extra_context=None):
        is_preview = bool(request.GET.get('preview'))
        start_date = Task.objects.get(id=object_id).start_date
        if start_date:
            extra_context = {
                'show_save_and_continue': False
            }
        else:
            extra_context = {
                'show_save_and_continue': not is_preview,
                'show_preview': not is_preview,
                'show_publish': not is_preview,
                'show_back': is_preview
            }
        return super(TaskForAdmin, self).change_view(request, object_id,
                                                     form_url, extra_context=extra_context)

    def response_change(self, request, obj):
        opts = self.model._meta
        preserved_filters = self.get_preserved_filters(request)
        if '_preview' in request.POST:
            redirect_url = request.path + '?preview=true'
            redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
            return HttpResponseRedirect(redirect_url)
        elif '_publish' in request.POST:
            msg_dict = {'name': force_text(opts.verbose_name), 'obj': force_text(obj.title)}
            msg = _('You published the %(name)s "%(obj)s"!') % msg_dict
            self.message_user(request, msg, messages.SUCCESS)
            return self.response_post_save_change(request, obj)
        else:
            return super(TaskForAdmin, self).response_change(request, obj)


def user_is_admin(user):
    return user.groups.filter(name='admins').exists()


class Dashboard(admin.ModelAdmin):
    form = CustomForm
    list_display = ('type', 'name', 'time_started', 'time_left_or_ended', 'status')
    list_display_links = ('name',)
    readonly_fields = (
        'time_left_or_ended', 'time_started', 'status', 'name', 'description', 'requirements', 'submission_type',
        'expected_results', 'deadline', 'extra_material',)
    fields = ['name', 'description', 'requirements', 'submission_type', 'time_started', 'deadline',
              'time_left_or_ended',
              'expected_results', 'extra_material', 'summary_pitch', 'body', 'conclusion', 'references', 'videos']
    can_delete = False
    actions = None
    formfield_overrides = {TextField: {'widget': SummernoteWidget()}}

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def get_list_display(self, request):
        list_display = super(Dashboard, self).get_list_display(request)
        if user_is_admin(request.user) and 'user' not in list_display:
            list_display = ('user',) + list_display
        return list_display

    def time_left_or_ended(self, obj):
        if obj.status == InternTask.UNFINISHED:
            if not overtime(obj):
                s = calculate_time_left(obj)
                hours, remainder = divmod(s, 3600)
                minutes, seconds = divmod(remainder, 60)
                return '<div id="countdown"></div>%d:%d:%d' % (int(hours), int(minutes), int(seconds))
            else:
                return "Overtime!"
        else:
            return obj.time_ended

    time_left_or_ended.allow_tags = True

    def get_queryset(self, request):
        queryset = super(Dashboard, self).get_queryset(request)
        is_admin = user_is_admin(request.user)
        if is_admin:
            return queryset
        else:
            return queryset.filter(user=request.user)

    def get_form(self, request, obj=None, **kwargs):
        modelform = super(Dashboard, self).get_form(request, obj, **kwargs)

        class ModelFormMetaClass(modelform):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return modelform(*args, **kwargs)

        return ModelFormMetaClass

    def get_readonly_fields(self, request, obj=None):
        if show_interntask_as_readonly(obj=obj, request=request):
            return self.readonly_fields + (
                'summary_pitch_safe', 'body_safe', 'conclusion_safe', 'reference_urls', 'video_urls',)
        return self.readonly_fields

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(Dashboard, self).get_fieldsets(request, obj)
        if show_interntask_as_readonly(obj=obj, request=request):
            fields_ = fieldsets[0][1]['fields']
            fields_ = [item for item in fields_ if
                       item not in ['summary_pitch', 'body', 'conclusion', 'references', 'videos']]
            fieldsets[0][1].update({'fields': fields_})
            fieldsets[0][1]['fields'].extend(
                ['summary_pitch_safe', 'body_safe', 'conclusion_safe', 'reference_urls', 'video_urls'])
        return fieldsets

    def change_view(self, request, object_id, form_url='', extra_context=None):
        status = InternTask.objects.get(id=object_id).status
        if status == models.InternTask.UNFINISHED\
                and not overtime(object_id):
            is_preview = bool(request.GET.get('preview'))
            extra_context = {
                'show_save_and_continue': not is_preview,
                'show_abandon': not is_preview,
                'show_accept': False,
                'show_preview': not is_preview,
                'show_submit': is_preview,
                'show_back': is_preview
            }
        else:
            extra_context = {
                'show_save_and_continue': False,
                'show_abandon': False,
                'show_accept': False,
                'show_preview': False,
                'show_submit': False,
                'show_back': False
            }

        return super(Dashboard, self).change_view(request, object_id,
                                                  form_url, extra_context=extra_context)

    def response_change(self, request, obj):
        opts = self.model._meta
        preserved_filters = self.get_preserved_filters(request)
        if not overtime(obj.id):
            if '_abandon' in request.POST:
                obj.status = models.InternTask.ABANDONED
                obj.time_ended = timezone.now()
                obj.save()
                msg_dict = {'name': force_text(opts.verbose_name), 'obj': force_text(obj.task.title)}
                msg = _('The %(name)s "%(obj)s" was abandoned!') % msg_dict
                self.message_user(request, msg, messages.WARNING)
                return self.response_post_save_change(request, obj)
            elif '_preview' in request.POST:
                redirect_url = request.path + '?preview=true'
                redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
                return HttpResponseRedirect(redirect_url)
            elif '_submit' in request.POST:
                obj.status = models.InternTask.FINISHED
                obj.time_ended = timezone.now()
                obj.save()
                msg_dict = {'name': force_text(opts.verbose_name), 'obj': force_text(obj.task.title)}
                msg = _('You submitted the %(name)s "%(obj)s"!') % msg_dict
                self.message_user(request, msg, messages.SUCCESS)
                return self.response_post_save_change(request, obj)
            else:
                return super(Dashboard, self).response_change(request, obj)
        else:
            return super(Dashboard, self).response_change(request, obj)


class TagAdmin(admin.ModelAdmin):
    pass


class TypeAdmin(admin.ModelAdmin):
    list_display = ('name',)


class LogAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'content_type', 'object', 'change_message')
    list_display_links = ('action_time', )
    fields = ['action_time', 'user', 'content_type', 'object', 'change_message']
    readonly_fields = ('action_time', 'user', 'content_type', 'object', 'change_message',)

    can_delete = False
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        queryset = super(LogAdmin, self).get_queryset(request)
        interns_group_id = Group.objects.get(name='interns').id
        intern_user_ids = User.objects.filter(groups__name='interns')
        # # show only log entries that interns have made
        # if request.user.groups.filter(name='admins').exists():
        #     return queryset
        # else:
        return queryset.filter(user_id__in=intern_user_ids)

    def user(self, obj):
        return User.objects.get(id=obj.user_id)

    def content_type(self, obj):
        return ContentType.objects.get(id=obj.content_type_id)

    def object(self, obj):
        label = obj.object_repr
        object_url = reverse('admin:%s_%s_change' %
                       ('sidrun', 'interntask'),
                       args=(obj.object_id,),
                       current_app=self.admin_site.name)
        return '<a href="%s">%s</a>' % (object_url, label)
    object.allow_tags = True


class HelpTextAdmin(admin.ModelAdmin):
    list_display = ('heading', 'content')


class HelpTextForAdmin(HelpTextAdmin):
    formfield_overrides = {TextField: {'widget': SummernoteWidget()}, CharField: {'widget': SummernoteWidget()}}


class HelpTextForIntern(HelpTextAdmin):
    actions = None
    readonly_fields = ('heading', 'content')

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = {
            'show_save_and_continue': False
        }
        return super(HelpTextForIntern, self).change_view(request, object_id,
                                                     form_url, extra_context=extra_context)


admin.site.register(LogEntry, LogAdmin)
admin.site.register(InternTask, Dashboard)
admin.site.register(Task, ViewNewTasks)
admin.site.register(AdminTask, TaskForAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(HelpText, HelpTextForIntern)
admin.site.register(AdminHelpText, HelpTextForAdmin)