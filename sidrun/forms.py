import re
import datetime

from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.encoding import force_text
from django.forms.models import BaseInlineFormSet
from django.utils.html import strip_tags

from django import forms
from sidrun.models import Tag


class CustomSelectMultipleTags(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class AddTaskForm(forms.ModelForm):
    tags = CustomSelectMultipleTags(widget=forms.CheckboxSelectMultiple, queryset=Tag.objects.all())

    def clean(self):
        data = super(AddTaskForm, self).clean()
        unpublish_date_ = self.cleaned_data.get("unpublish_date")
        publish_date_ = self.cleaned_data.get("publish_date")
        try:
            hours_between_dates = (unpublish_date_ - publish_date_).total_seconds()/60
        except TypeError:
            hours_between_dates = None
        validation_errors = []
        time_to_complete_task = self.cleaned_data.get("time_to_complete_task")
        if time_to_complete_task is not None and hours_between_dates is not None and time_to_complete_task > hours_between_dates:
            validation_errors.append(ValidationError("Time to complete task has to fit between publish and unpublish dates!"))
        if publish_date_ and unpublish_date_ and publish_date_ > unpublish_date_:
            validation_errors.append(ValidationError("The unpublish date must be after the publish date!"))
        if validation_errors:
            raise ValidationError(validation_errors)
        return data

    def clean_publish_date(self):
        published_date = self.cleaned_data.get("publish_date")
        if published_date and published_date.date() < timezone.now().date():
            raise ValidationError("Please enter a date that is not in the past!")
        return published_date

    def clean_unpublish_date(self):
        unpublished_date = self.cleaned_data.get("unpublish_date")
        if unpublished_date and unpublished_date < timezone.now():
            raise ValidationError("Please enter a date that is not in the past!")
        return unpublished_date


class CustomInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(CustomInlineFormSet, self).__init__(*args, **kwargs)
        self.regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
            r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    def need_to_validate(self):
        return '_preview' in self.request.POST

    def clean(self):
        inline_formset_data = super(CustomInlineFormSet, self).clean()
        if self.need_to_validate():
            for form in self.forms:
                data = form.clean()
                summary_pitch = data['summary_pitch']
                validation_errors = []
                min_summary_length = 140
                summary_length = len(strip_tags(summary_pitch))
                if summary_length < min_summary_length:
                    validation_errors.append(ValidationError("Summary pitch length needs to be at least %d characters. You have %d." % (min_summary_length,
                                                                                                                                        summary_length)))
                body = data['body']
                min_body_length = 280
                body_length = len(strip_tags(body))
                if body_length < min_body_length:
                    validation_errors.append(ValidationError("Body length needs to be at least %d characters. You have %d." % (min_body_length,
                                                                                                                               body_length)))
                conclusion = data['conclusion']
                min_conclusion_length = 140
                conclusion_length = len(strip_tags(conclusion))
                if conclusion_length < min_conclusion_length:
                    validation_errors.append(ValidationError("Conclusion length needs to be at least %d characters. You have %d." % (min_conclusion_length,
                                                                                                                                     conclusion_length)))
                references = data['references']
                references_prepared_for_validation = re.findall(r'href=[\'"]?([^\'" >]+)', references)
                if not references_prepared_for_validation:
                    validation_errors.append(ValidationError("There needs to be at least one url address in references!"))
                for reference in references_prepared_for_validation:
                    if not self.regex.search(force_text(reference)):
                        validation_errors.append(ValidationError("References need to be valid URL addresses."))
                videos = data['videos']
                video_urls_prepared_for_validation = re.findall(r'href=[\'"]?([^\'" >]+)', videos)
                if not video_urls_prepared_for_validation:
                    validation_errors.append(ValidationError("There needs to be at least one video url address in videos!"))
                for video in video_urls_prepared_for_validation:
                    if not self.regex.search(force_text(video)):
                        validation_errors.append(ValidationError("Videos need to be valid URL addresses."))
                raise ValidationError(validation_errors)
        return inline_formset_data