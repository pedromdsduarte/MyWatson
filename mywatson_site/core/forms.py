from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms.widgets import PasswordInput, TextInput
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


##############################################################
#   LOGIN FORM
##############################################################


class CustomAuthForm(AuthenticationForm):
    username = forms.CharField(widget=TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=PasswordInput(attrs={'placeholder':'Password'}))


##############################################################
#   REGISTRATION FORM
##############################################################

class SignupForm(UserCreationForm):
    email = forms.EmailField(widget=TextInput(attrs={'placeholder': 'Email'}), max_length=200, help_text='Required')
    username = forms.CharField(widget=TextInput(attrs={'placeholder': 'Username'}))
    password1 = forms.CharField(widget=PasswordInput(attrs={'placeholder':'Password'}))
    password2 = forms.CharField(widget=PasswordInput(attrs={'placeholder':'Repeat password'}))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')

        username = self.cleaned_data.get('username')
        if email and User.objects.filter(email=email).exclude(username=username).exists():
            raise forms.ValidationError(u'This email is already in use')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        return username
