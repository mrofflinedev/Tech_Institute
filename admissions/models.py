from django.db import models
from django.conf import settings
from courses.models import Course

class Enrollment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved / Active'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='enrollments'
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    fee_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    @property
    def fee_balance(self):
        return self.course.tuition_fee - self.fee_paid

    def __str__(self):
        return f"{self.student.username} -> {self.course.code} ({self.status})"
