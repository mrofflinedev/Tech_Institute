from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone_number = models.CharField(
        max_length=15, 
        unique=True,
        null=True,
        blank=True,
        help_text="Format: +2547XXXXXXXX for M-Pesa"
    )
    admission_number = models.CharField(max_length=30, unique=True, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.phone_number == "":
            self.phone_number = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = 'admin'
            self.is_staff = True
            self.admission_number = None
        super().save(*args, **kwargs)
