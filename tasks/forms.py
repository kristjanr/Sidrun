from django import forms
from task_admin.models import Tag


class CustomSelectMultipleTags(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class AddTypeAndTagsForms(forms.ModelForm):
    tags = CustomSelectMultipleTags(widget=forms.CheckboxSelectMultiple, queryset=Tag.objects.all())