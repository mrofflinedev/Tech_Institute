from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from courses.models import Course
from .models import Enrollment

@login_required
def apply_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.user.role != 'student':
        messages.error(request, "Only student accounts can apply for courses.")
        return redirect('courses:course_list')

    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user,
        course=course,
        defaults={'status': 'pending'}
    )

    if created:
        messages.success(request, f"Application submitted for {course.code} - {course.title}! Awaiting admin approval.")
    else:
        messages.info(request, f"You have already applied for {course.title} (Status: {enrollment.get_status_display()}).")

    return redirect('admissions:my_applications')

@login_required
def my_applications(request):
    applications = Enrollment.objects.filter(student=request.user).select_related('course').order_by('-enrolled_at')
    return render(request, 'admissions/my_applications.html', {'applications': applications})
