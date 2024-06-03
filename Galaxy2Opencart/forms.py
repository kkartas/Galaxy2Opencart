from django import forms
from .models import UserAnswer

class UserAnswerForm(forms.ModelForm):
    class Meta:
        model = UserAnswer
        fields = '__all__'