from django import forms
from .models import Photo


class ImageUploadForm(forms.ModelForm):

    class Meta:
        model = Photo
        exclude = ['user']
