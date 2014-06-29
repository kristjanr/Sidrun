from django.core.validators import MinLengthValidator, MinValueValidator
from django.db import models
from django.utils.safestring import mark_safe


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
    title = models.CharField(max_length=140, help_text='The heading for the task')
    type = models.ForeignKey(Type)
    tags = models.ManyToManyField(Tag, help_text='Add tags that relate to the task')
    description = models.TextField(max_length=5000, validators=[MinLengthValidator(280), ],
                                   help_text='An explanation or a description of the task. ')
    requirements = models.TextField(max_length=5000, validators=[MinLengthValidator(140)],
                                    help_text='An explanation or a description of the task requirements. For example "Must contain solutions from peer-reviewed articles".')

    VIDEO = 'MR'
    TEXT = 'TX'
    BOTH = 'BO'
    SUBMISSION_TYPE = (
        (VIDEO, 'Video'),
        (TEXT, 'Text'),
        (BOTH, 'Both')
    )
    submission_type = models.CharField(max_length=2,
                                       choices=SUBMISSION_TYPE,
                                       help_text='Select submission type')

    application_deadline = models.DateField(help_text='Set the application deadline')
    start_date = models.DateField()
    finish_date = models.DateField()
    number_of_positions_available = models.IntegerField(validators=[MinValueValidator(1)],
                                                        help_text='The number of positions available to the task.')
    expected_results = models.TextField(max_length=1000, validators=[MinLengthValidator(280)],
                                        help_text='This field should be used as an explanation or a description of the expected results the task creator has in mind for the task.')

    def __unicode__(self):
        return self.title

    def tags_list(self):
        return ', '.join([a.name for a in self.tags.all()])


class ExecuteTask(Task):
    class Meta:
        proxy = True
        verbose_name = 'new task'
        verbose_name_plural = 'new tasks'


class CreateTask(Task):
    class Meta:
        proxy = True
        verbose_name = 'created task'
        verbose_name_plural = 'created tasks'
