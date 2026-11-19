from django.contrib import admin
from .models import StudyMaterial, Assignment, Submission, ExamResult, ClassSchedule, Announcement

admin.site.register(StudyMaterial)
admin.site.register(Assignment)
admin.site.register(Submission)
admin.site.register(ExamResult)
admin.site.register(ClassSchedule)
admin.site.register(Announcement)
