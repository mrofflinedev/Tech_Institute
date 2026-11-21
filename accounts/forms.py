import re
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


    def clean_first_name(self):
        val = (self.cleaned_data.get('first_name') or '').strip()
        if not val or not re.match(r'^[A-Za-z\s]+$', val):
            raise forms.ValidationError('First name must contain only letters and spaces.')
        return ' '.join(val.split())

    def clean_last_name(self):
        val = (self.cleaned_data.get('last_name') or '').strip()
        if not val or not re.match(r'^[A-Za-z\s]+$', val):
            raise forms.ValidationError('Last name must contain only letters and spaces.')
        return ' '.join(val.split())

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise forms.ValidationError('Email address is required.')
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('This email address is already registered to another student.')
        return email

    def clean_password1(self):
        pwd = self.cleaned_data.get('password1') or ''
        if len(pwd) < 8 or not re.search(r'[A-Za-z]', pwd) or not re.search(r'[0-9]', pwd) or not re.search(r'[^A-Za-z0-9\s]', pwd):
            raise forms.ValidationError('Password must be at least 8 characters and include letters, numbers, and symbols (e.g. @, #, $).')
        return pwd


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
