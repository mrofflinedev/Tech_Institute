from datetime import datetime, timedelta, date
from django.db import models
from django.conf import settings
from courses.models import Course


class StudyMaterial(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='study_materials/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course.code} - {self.title}"


class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    instructions = models.TextField()
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course.code} - {self.title}"


class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'}
    )
    submitted_file = models.FileField(upload_to='submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.CharField(max_length=10, blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('assignment', 'student')

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"


class ExamResult(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='exam_results'
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    cat_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    exam_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('student', 'course')

    @property
    def total_score(self):
        return self.cat_score + self.exam_score

    @property
    def grade(self):
        total = self.total_score
        if total >= 70:
            return 'A'
        elif total >= 60:
            return 'B'
        elif total >= 50:
            return 'C'
        elif total >= 40:
            return 'D'
        return 'F'

    def __str__(self):
        return f"{self.student.username} - {self.course.code}: {self.grade}"


class ClassSchedule(models.Model):
    DAY_CHOICES = (
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.CharField(max_length=15, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField(editable=False)
    room_or_link = models.CharField(max_length=100, help_text="e.g. Lab 2 or Zoom Link")

    class Meta:
        ordering = ['day_of_week', 'start_time']

    def save(self, *args, **kwargs):
        start_dt = datetime.combine(date.today(), self.start_time)
        self.end_time = (start_dt + timedelta(hours=3)).time()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.course.code} - {self.day_of_week} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"
class Announcement(models.Model):
    AUDIENCE_CHOICES = (
        ('all', 'Everyone (Institute-Wide)'),
        ('students', 'Students Only'),
        ('instructors', 'Instructors Only'),
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Leave blank for a general institute-wide notice."
    )
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default='all')
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
