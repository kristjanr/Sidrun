from django.contrib import admin

from task_admin.models import Tag, Type, ViewTasks, ChangeTasks, TaskForInternFullInfo
from tasks.forms import AddTypeAndTagsForms

from django.contrib.admin.templatetags.admin_modify import *
from django.contrib.admin.templatetags.admin_modify import submit_row as original_submit_row
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


class TaskFullInfo(TaskLessInfo):
    readonly_fields = TaskLessInfo.readonly_fields + ['expected_results', 'extra_material']
    fields = TaskLessInfo.fields + ['expected_results', 'extra_material']


class ForAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'type', 'tags_list', 'submission_type', 'application_deadline', 'start_date', 'finish_date',
        'number_of_positions',)
    form = AddTypeAndTagsForms


class AddTag(admin.ModelAdmin):
    list_display = ('name',)


class AddType(admin.ModelAdmin):
    list_display = ('name',)


admin.site.register(TaskForInternFullInfo, TaskFullInfo)
admin.site.register(ViewTasks, TaskLessInfo)
admin.site.register(ChangeTasks, ForAdmin)
admin.site.register(Tag, AddTag)
admin.site.register(Type, AddType)