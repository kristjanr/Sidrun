from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MinValueValidator, URLValidator
from django.db import models
from django.db.models.signals import post_save
from django.utils import timezone
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

    time_to_complete_task = models.IntegerField(validators=[MinValueValidator(1)],
                                                help_text='Maximum hours given to complete the task.')
    publish_date = models.DateTimeField()
    unpublish_date = models.DateTimeField()
    number_of_positions = models.IntegerField(validators=[MinValueValidator(1)],
                                              help_text='The number of positions available.')
    expected_results = models.TextField(max_length=1000, validators=[MinLengthValidator(280)])

    extra_material = models.TextField(null=True)

    def number_of_current_positions(self):
        return self.number_of_positions - self.interntask_set.exclude(status=InternTask.ABANDONED).__len__()

    def time_left(self):
        return self.interntask_set.first().time_left()

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
    conclusion = models.TextField(null=True, blank=True)
    references = models.TextField(null=True, blank=True)
    videos = models.TextField(null=True, blank=True)

    def summary_pitch_safe(self):
        return mark_safe(self.summary_pitch)

    summary_pitch_safe.short_description = "Summary pitch"

    def body_safe(self):
        return mark_safe(self.body)

    body_safe.short_description = "Body"

    def conclusion_safe(self):
        return mark_safe(self.conclusion)

    conclusion_safe.short_description = "Conclusion"

    def reference_urls(self):
        return mark_safe(self.references)

    reference_urls.short_description = "References"

    def video_urls(self):
        return mark_safe(self.videos)

    video_urls.short_description = "Videos"

    def __unicode__(self):
        return self.user.get_username() + "'s task " + self.task.title

    def task_type(self):
        return self.task.type

    def task_name(self):
        return self.task.title

    def time_left(self):
        s = (timezone.now() - self.date_started).total_seconds()
        hours, remainder = divmod(s, 3600)
        minutes, seconds = divmod(remainder, 60)
        return '%d:%d:%d' % (int(hours), int(minutes), int(seconds))

    class Meta:
        unique_together = ('task', 'user',)
        verbose_name = 'Accepted task'
        verbose_name_plural = 'Dashboard'