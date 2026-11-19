from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Institute Profile', {'fields': ('role', 'phone_number', 'admission_number', 'profile_picture')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Institute Profile', {'fields': ('role', 'phone_number', 'admission_number')}),
    )

admin.site.register(User, CustomUserAdmin)
