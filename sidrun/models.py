from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MinValueValidator, URLValidator
from django.db import models
from django.db.models.signals import post_save
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

    verbose_name = 'new task'


class AdminTask(Task):
    class Meta:
        proxy = True
        verbose_name = 'admin task'
        verbose_name_plural = 'admin tasks'


class Profile(models.Model):
    allowed_number_of_tasks = models.IntegerField(default=1)
    user = models.OneToOneField(User)

    def __str__(self):
        return "%s's profile" % self.user


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile, created = Profile.objects.get_or_create(user=instance)

post_save.connect(create_user_profile, sender=User)


class InternTask(models.Model):
    task = models.ForeignKey(to=Task)
    user = models.ForeignKey(to=User)
    UNFINISHED = 'UF'
    UNSUBMITTED = 'US'
    FINISHED = 'FI'
    ABANDONED = 'AB'
    STATUSES = (
        (UNFINISHED, 'Unfinished'),
        (UNSUBMITTED, 'Unsubmitted'),
        (FINISHED, 'Finished'),
        (ABANDONED, 'Abandoned')
    )
    status = models.CharField(max_length=2, choices=STATUSES)
    date_started = models.DateTimeField(auto_now_add=True)
    summary_pitch = models.TextField(null=True, blank=True)
    body = models.TextField(null=True, blank=True)
    conclusion = models.TextField( null=True, blank=True)
    # TODO Add more button http://stackoverflow.com/questions/6142025/dynamically-add-field-to-a-form
    references = models.CharField(max_length=100, null=True, blank=True)
    video = models.CharField(max_length=100, null=True, blank=True)

    def summary_pitch_safe(self):
        return mark_safe(self.summary_pitch)
    summary_pitch_safe.short_description = "Summary pitch"

    def body_safe(self):
        return mark_safe(self.body)
    body_safe.short_description = "Body"

    def conclusion_safe(self):
        return mark_safe(self.conclusion)
    conclusion_safe.short_description = "Conclusion"

    def references_url(self):
        return '<a href="%s">%s</a>' % (self.references, self.references)
    references_url.allow_tags = True
    references_url.short_description = "References"

    def video_url(self):
        return '<a href="%s">%s</a>' % (self.video, self.video)
    video_url.allow_tags = True
    video_url.short_description = "Video"

    def __unicode__(self):
        return self.user.get_username() + "'s task " + self.task.title

    def task_type(self):
        return self.task.type

    def task_name(self):
        return self.task.title

    class Meta:
        unique_together = ('task', 'user',)