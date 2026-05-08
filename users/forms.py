from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import CustomUser


class RegisterForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ["username", "password1", "password2"]


class EditProfileForm(forms.ModelForm):
    bio = forms.CharField(widget=forms.Textarea, required=False, label="About myself")
    avatar = forms.ImageField(required=False, label="Avatar")
    email = forms.EmailField(required=True, label="Just Email")

    class Meta:
        model = CustomUser
        fields = ["bio", "avatar", "email"]


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
