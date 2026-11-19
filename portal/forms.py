from django import forms
from courses.models import Course, TeamMember
from .models import StudyMaterial, Assignment, Submission, ExamResult, ClassSchedule, Announcement


class StudyMaterialForm(forms.ModelForm):
    class Meta:
        model = StudyMaterial
        fields = ['course', 'title', 'file']


class AssignmentForm(forms.ModelForm):
    due_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )

    class Meta:
        model = Assignment
        fields = ['course', 'title', 'instructions', 'due_date']


class GradeSubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['grade', 'feedback']


class ExamResultForm(forms.ModelForm):
    class Meta:
        model = ExamResult
        fields = ['student', 'course', 'cat_score', 'exam_score']


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['code', 'title', 'description', 'duration_months', 'tuition_fee', 'instructor']


class ClassScheduleForm(forms.ModelForm):
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        help_text="End time is automatically set to 3 hours after start time."
    )

    class Meta:
        model = ClassSchedule
        fields = ['course', 'day_of_week', 'start_time', 'room_or_link']


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'course', 'audience', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write your notice here...'}),
        }


class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = ['full_name', 'role_title', 'bio', 'photo', 'display_order']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Short bio and expertise...'}),
        }
