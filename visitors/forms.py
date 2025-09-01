from django import forms
from .models import Visitor

class VisitorForm(forms.ModelForm):
    class Meta:
        model = Visitor
        fields = ["name", "email", "phone", "purpose", "image"]  # all required fields
