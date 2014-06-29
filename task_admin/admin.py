from django.contrib import admin

from task_admin.models import Task, Tag, Type, ExecuteTask, CreateTask
from tasks.forms import AddTypeAndTagsForms


class ViewNewTasks(admin.ModelAdmin):
    list_display = ('title', 'type', 'number_of_positions_available', 'application_deadline')
    readonly_fields = ['requirements', 'description', 'finish_date', 'title', 'type', 'start_date', 'expected_results',
                       'number_of_positions_available', 'submission_type', 'application_deadline']


class CreateTasks(admin.ModelAdmin):
    list_display = (
        'title', 'type', 'tags_list', 'submission_type', 'application_deadline', 'start_date', 'finish_date',
        'number_of_positions_available',)
    form = AddTypeAndTagsForms


class AddTag(admin.ModelAdmin):
    list_display = ('name',)


class AddType(admin.ModelAdmin):
    list_display = ('name',)


admin.site.register(ExecuteTask, ViewNewTasks)
admin.site.register(CreateTask, CreateTasks)
admin.site.register(Tag, AddTag)
admin.site.register(Type, AddType)