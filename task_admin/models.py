from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MinValueValidator, URLValidator
from django.db import models

from task_admin.validators import YoutubeURLValidator


class Type(models.Model):
    name = models.CharField(max_length=25, unique=True)
    icon = models.ImageField(upload_to='./type_icons/', null=True)

    def __unicode__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=25, unique=True)

    def __unicode__(self):
        return self.name


class Task(models.Model):
    title = models.CharField(max_length=140)
    type = models.ForeignKey(Type)
    tags = models.ManyToManyField(Tag)
    description = models.TextField(max_length=5000, validators=[MinLengthValidator(280), ])
    requirements = models.TextField(max_length=5000, validators=[MinLengthValidator(140)])

    VIDEO = 'MR'
    TEXT = 'TX'
    BOTH = 'BO'
    SUBMISSION_TYPE = (
        (VIDEO, 'Video'),
        (TEXT, 'Text'),
        (BOTH, 'Both')
    )
    submission_type = models.CharField(max_length=2,
                                       choices=SUBMISSION_TYPE)

    application_deadline = models.DateField()
    start_date = models.DateField()
    finish_date = models.DateField()
    number_of_positions = models.IntegerField(validators=[MinValueValidator(1)],
                                                        help_text='The number of positions available.')
    number_of_current_positions = models.IntegerField(help_text='The number of current positions available.')
    expected_results = models.TextField(max_length=1000, validators=[MinLengthValidator(280)])

    extra_material = models.TextField(null=True)

    def __unicode__(self):
        return self.title

    def tags_list(self):
        return ', '.join([a.name for a in self.tags.all()])

    def type_icon(self):
            return '<img src="%s"/>' % self.type.icon.url
    type_icon.allow_tags = True


class TaskForInternFullInfo(Task):
    class Meta:
        proxy = True
        verbose_name = 'Task full info'
        verbose_name_plural = 'Tasks, full info'


class ViewTasks(Task):
    class Meta:
        proxy = True
        verbose_name = 'task'
        verbose_name_plural = 'tasks'


class ChangeTasks(Task):
    class Meta:
        proxy = True
        verbose_name = 'task'
        verbose_name_plural = 'tasks'


class InternTask(models.Model):
    task = models.ForeignKey(to=Task)
    user = models.ForeignKey(to=User)
    UNFINISHED = 'UF'
    UNSUBMITTED = 'US'
    FINISHED = 'FI'
    STATUSES = (
        (UNFINISHED, 'Unfinished'),
        (UNSUBMITTED, 'Unsubmitted'),
        (FINISHED, 'Finished')
    )
    status = models.CharField(max_length=2, choices=STATUSES)
    #TODO RichTextEditor http://stackoverflow.com/questions/329963/replace-textarea-with-rich-text-editor-in-django-admin
    summary_pitch = models.TextField(validators=[MinLengthValidator(140)])
    body = models.TextField(validators=[MinLengthValidator(280)])
    conclusion = models.TextField(validators=[MinLengthValidator(140)])
    # TODO Add more button http://stackoverflow.com/questions/6142025/dynamically-add-field-to-a-form
    references = models.TextField(validators=[URLValidator()])
    video = models.TextField(validators=[YoutubeURLValidator()])

