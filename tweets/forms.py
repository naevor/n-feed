from django import forms
from django.core.exceptions import ValidationError as DjangoValidationError

from twitmain.uploads import validate_tweet_media_upload

from .models import Comment, Tweet


class TweetForm(forms.ModelForm):
    class Meta:
        model = Tweet
        fields = ["content", "media"]
        widgets = {
            "content": forms.Textarea(
                attrs={"placeholder": "What's new?", "rows": 3, "class": "form-control"}
            ),
        }

    def clean_content(self):
        content = self.cleaned_data.get("content")
        if len(content) > 280:
            raise forms.ValidationError("Tweet cannot contain more than 280 characters.")
        return content

    def clean_media(self):
        media = self.cleaned_data.get("media")
        if media:
            try:
                validate_tweet_media_upload(media)
            except DjangoValidationError as exc:
                raise forms.ValidationError(exc.messages) from exc
        return media


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={"placeholder": "wright a comment...", "rows": 2, "class": "form-control"}
            ),
        }

    def clean_content(self):
        content = self.cleaned_data.get("content")
        if len(content) > 150:
            raise forms.ValidationError("Comments cannot contain more than 150 characters.")
        return content
