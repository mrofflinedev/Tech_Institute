from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Course, ContactMessage, TeamMember
from admissions.models import Enrollment


def about_us(request):
    featured_courses = Course.objects.all().order_by('code')[:3]
    total_courses = Course.objects.count()
    team_members = TeamMember.objects.all()
    return render(request, 'courses/about_us.html', {
        'featured_courses': featured_courses,
        'total_courses': total_courses,
        'team_members': team_members,
    })


def contact_us(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        subject = request.POST.get('subject', '').strip()
        message_text = request.POST.get('message', '').strip()

        if full_name and email and subject and message_text:
            ContactMessage.objects.create(
                full_name=full_name,
                email=email,
                phone_number=phone_number,
                subject=subject,
                message=message_text,
            )
            messages.success(request, "Thank you for contacting TECH INSTITUTE! Our admissions team will reach out shortly.")
            return redirect('courses:contact_us')
        else:
            messages.error(request, "Please fill in all required fields.")

    return render(request, 'courses/contact_us.html')


def course_list(request):
    courses = Course.objects.all().order_by('code')
    enrolled_course_ids = []
    if request.user.is_authenticated:
        enrolled_course_ids = list(
            Enrollment.objects.filter(student=request.user).values_list('course_id', flat=True)
        )
    return render(request, 'courses/course_list.html', {
        'courses': courses,
        'enrolled_course_ids': enrolled_course_ids,
    })


def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrollment = None
    if request.user.is_authenticated:
        enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'enrollment': enrollment,
    })
