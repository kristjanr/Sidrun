from django.contrib import admin

from task_admin.models import Tag, Type, TaskForInternLessInfo, TaskForAdmin, TaskForInternFullInfo
from tasks.forms import AddTypeAndTagsForms


class TaskLessInfo(admin.ModelAdmin):
    list_display = ('title', 'type', 'type_icon', 'number_of_current_positions', 'start_date')
    readonly_fields = ['title', 'tags_list', 'type', 'type_icon', 'description', 'requirements', 'submission_type', 'start_date',
                       'finish_date', 'number_of_current_positions']
    fields = ['title', 'type', 'description', 'requirements', 'submission_type', 'start_date',
                       'finish_date', 'number_of_current_positions']


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
admin.site.register(TaskForInternLessInfo, TaskLessInfo)
admin.site.register(TaskForAdmin, ForAdmin)
admin.site.register(Tag, AddTag)
admin.site.register(Type, AddType)