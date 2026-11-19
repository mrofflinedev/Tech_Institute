from django.db import models
from django.conf import settings

class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)  # e.g., CS101
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration_months = models.PositiveIntegerField(default=6)
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2)
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'instructor'},
        related_name='taught_courses'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.title}"
class ContactMessage(models.Model):
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.full_name} - {self.subject}"
class TeamMember(models.Model):
    full_name = models.CharField(max_length=120)
    role_title = models.CharField(max_length=120, help_text="e.g. Principal, Lead Software Instructor, Academic Registrar")
    bio = models.TextField(help_text="Short description of background and expertise")
    photo = models.ImageField(upload_to='team_photos/', blank=True, null=True)
    display_order = models.PositiveIntegerField(default=1, help_text="Lower numbers appear first")

    class Meta:
        ordering = ['display_order', 'full_name']

    def __str__(self):
        return f"{self.full_name} - {self.role_title}"
