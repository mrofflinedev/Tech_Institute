from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class StudentRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        help_text="Enter M-Pesa number in format 2547XXXXXXXX"
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number']

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        if phone.startswith('07') or phone.startswith('01'):
            phone = '254' + phone[1:]
        elif phone.startswith('+254'):
            phone = phone[1:]
        return phone

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'profile_picture']

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        if phone.startswith('07') or phone.startswith('01'):
            phone = '254' + phone[1:]
        elif phone.startswith('+254'):
            phone = phone[1:]
        return phone
