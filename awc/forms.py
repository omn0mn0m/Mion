from django import forms

from .models import Challenge

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

class CreateChallengeForm(forms.Form):
    thread_id = forms.IntegerField(help_text="Challenge Thread ID")
    category = forms.ChoiceField(choices=Challenge.CATEGORY_CHOICES, help_text="Challenge Category")
    challenge_code = forms.CharField(widget=forms.Textarea(attrs={"rows":20, "cols":100}),
                                     help_text="Challenge Code")
    
    def clean_thread_id(self):
        """Cleans the thread_id value"""
        data = self.cleaned_data['thread_id']

        if data < 0:
            raise ValidationError(_("Invaid thread id - must be a positive value"))

        return data

    def clean_challenge_code(self):
        """Cleans the challenge_code value"""
        data = self.cleaned_data['challenge_code']

        return data

    def clean_category(self):
        """Cleans the category value"""
        data = self.cleaned_data['category']

        return data

class AddExistingSubmissionForm(forms.Form):
    challenge = forms.ModelChoiceField(queryset=Challenge.objects.all())
    comment_id = forms.IntegerField()

    def clean_challenge(self):
        """ Cleans the challenge value"""
        data = self.cleaned_data['challenge']

        return data

    def clean_comment_id(self):
        """Cleans the thread_id value"""
        data = self.cleaned_data['comment_id']

        if data < 0:
            raise ValidationError(_("Invaid comment id - must be a positive value"))

        return data

class RequirementForm(forms.Form):
    completed = forms.BooleanField(help_text="Completed Status")
    start = forms.CharField(help_text="Start Date")
    finish = forms.CharField(help_text="Finish Date")
    anime = forms.CharField(help_text="Anime Title")
    link = forms.CharField(help_text="Anime Link")
    extra = forms.CharField(help_text="Extra Info")

class BonusRequirementForm(forms.Form):
    completed = forms.BooleanField(help_text="Completed Status")
    start = forms.CharField(help_text="Start Date")
    finish = forms.CharField(help_text="Finish Date")
    anime = forms.CharField(help_text="Anime Title")
    link = forms.CharField(help_text="Anime Link")
    extra = forms.CharField(help_text="Extra Info")
