import re

from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.encoding import force_text
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
        deadline = self.cleaned_data.get("deadline")
        publish_date_ = self.cleaned_data.get("publish_date")
        try:
            hours_between_dates = (deadline - publish_date_).total_seconds() / 60
        except TypeError:
            hours_between_dates = None
        validation_errors = []
        time_to_complete_task = self.cleaned_data.get("time_to_complete_task")
        if time_to_complete_task is not None and hours_between_dates is not None and time_to_complete_task > hours_between_dates:
            validation_errors.append(
                ValidationError("Time to complete task has to fit between publish date and deadline!"))
        if publish_date_ and deadline and publish_date_ > deadline:
            validation_errors.append(ValidationError("The deadline must be after the publish date!"))
        if validation_errors:
            raise ValidationError(validation_errors)
        return data

    def clean_publish_date(self):
        published_date = self.cleaned_data.get("publish_date")
        if published_date and published_date.date() < timezone.now().date():
            raise ValidationError("Please enter a date that is not in the past!")
        return published_date

    def clean_deadline(self):
        deadline = self.cleaned_data.get("deadline")
        if deadline and deadline < timezone.now():
            raise ValidationError("Please enter a deadline that is not in the past!")
        return deadline


class CustomForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(CustomForm, self).__init__(*args, **kwargs)
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

    def clean_body(self):
        body = self.data.get("body") or ''
        if self.need_to_validate():
            min_body_length = 280
            body_length = len(strip_tags(body))
            if body_length < min_body_length:
                raise ValidationError(
                    "Body length needs to be at least %d characters. You have %d." % (min_body_length, body_length))
        return body

    def clean_summary_pitch(self):
        summary_pitch = self.data.get("summary_pitch") or ''
        if self.need_to_validate():
            min_summary_length = 140
            summary_length = len(strip_tags(summary_pitch))
            if summary_length < min_summary_length:
                raise ValidationError("Summary pitch length needs to be at least %d characters. You have %d." % (
                    min_summary_length, summary_length))
        return summary_pitch

    def clean_conclusion(self):
        conclusion = self.data.get("conclusion") or ''
        if self.need_to_validate():
            min_conclusion_length = 140
            conclusion_length = len(strip_tags(conclusion))
            if conclusion_length < min_conclusion_length:
                raise ValidationError("Conclusion length needs to be at least %d characters. You have %d." % (
                    min_conclusion_length, conclusion_length))
        return conclusion

    def clean_references(self):
        references = self.data.get("references")
        if self.need_to_validate():
            references_prepared_for_validation = re.findall(r'href=[\'"]?([^\'" >]+)', references)
            if not references_prepared_for_validation:
                raise ValidationError("There needs to be at least one url address in references. Please use the link icon to add one!")
            validation_errors = []
            for reference in references_prepared_for_validation:
                if not self.regex.search(force_text(reference)):
                    validation_errors.append(ValidationError("'%s' is not valid url address." % reference))
            if validation_errors:
                raise ValidationError(validation_errors)
        return references

    def clean_videos(self):
        videos = self.data.get("videos")
        if self.need_to_validate():
            video_urls_prepared_for_validation = re.findall(r'href=[\'"]?([^\'" >]+)', videos)
            if not video_urls_prepared_for_validation:
                raise ValidationError("There needs to be at least one url address in videos. Please use the link icon to add one!")
            validation_errors = []
            for video in video_urls_prepared_for_validation:
                if not self.regex.search(force_text(video)):
                    validation_errors.append(ValidationError("'%s' is not a valid url address." % video))
            if validation_errors:
                raise ValidationError(validation_errors)
        return videos