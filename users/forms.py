from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError as DjangoValidationError

from twitmain.uploads import validate_avatar_upload

from .models import CustomUser


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False, label="Email")

    class Meta:
        model = CustomUser
        fields = ["username", "email", "password1", "password2"]


class EditProfileForm(forms.ModelForm):
    bio = forms.CharField(widget=forms.Textarea, required=False, label="About myself")
    avatar = forms.ImageField(required=False, label="Avatar")
    email = forms.EmailField(required=True, label="Just Email")

    class Meta:
        model = CustomUser
        fields = ["bio", "avatar", "email"]

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar:
            try:
                validate_avatar_upload(avatar)
            except DjangoValidationError as exc:
                raise forms.ValidationError(exc.messages) from exc
        return avatar


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
