import os
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Sum, Q
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from admissions.models import Enrollment
from courses.models import Course, ContactMessage, TeamMember
from accounts.models import User
from payments.models import Transaction
from .models import StudyMaterial, Assignment, Submission, ExamResult, ClassSchedule, Announcement
from .forms import (
    StudyMaterialForm,
    AssignmentForm,
    GradeSubmissionForm,
    ExamResultForm,
    CourseForm,
    ClassScheduleForm,
    AnnouncementForm,
    TeamMemberForm,
)


@login_required
def student_dashboard(request):
    enrollments = Enrollment.objects.filter(student=request.user, status='approved').select_related('course')
    enrolled_courses = [enrollment.course for enrollment in enrollments]

    materials = StudyMaterial.objects.filter(course__in=enrolled_courses).select_related('course').order_by('-uploaded_at')
    assignments = Assignment.objects.filter(course__in=enrolled_courses).select_related('course').order_by('due_date')
    submissions = Submission.objects.filter(student=request.user).select_related('assignment')
    submission_map = {sub.assignment.id: sub for sub in submissions}
    results = ExamResult.objects.filter(student=request.user).select_related('course')
    schedules = ClassSchedule.objects.filter(course__in=enrolled_courses).select_related('course', 'course__instructor')
    announcements = Announcement.objects.filter(
        Q(course__isnull=True) | Q(course__in=enrolled_courses),
        audience__in=['all', 'students']
    ).select_related('course', 'posted_by')[:5]

    total_balance = sum(enrollment.fee_balance for enrollment in enrollments)
    pending_assignments_count = sum(1 for a in assignments if a.id not in submission_map)

    context = {
        'enrollments': enrollments,
        'materials': materials,
        'assignments': assignments,
        'submission_map': submission_map,
        'results': results,
        'schedules': schedules,
        'announcements': announcements,
        'total_balance': total_balance,
        'pending_assignments_count': pending_assignments_count,
    }
    return render(request, 'portal/dashboard.html', context)


@login_required
def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)

    if request.method == 'POST' and request.FILES.get('submitted_file'):
        uploaded_file = request.FILES['submitted_file']
        Submission.objects.update_or_create(
            assignment=assignment,
            student=request.user,
            defaults={'submitted_file': uploaded_file}
        )
        messages.success(request, f"Assignment '{assignment.title}' submitted successfully!")
        return redirect('portal:dashboard')

    return render(request, 'portal/submit_assignment.html', {'assignment': assignment})


@login_required
def download_transcript(request):
    results = ExamResult.objects.filter(student=request.user).select_related('course')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Transcript_{request.user.username}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.jpg')
    text_x = 50
    if os.path.exists(logo_path):
        p.drawImage(logo_path, 50, height - 140, width=120, height=120, preserveAspectRatio=True, mask='auto')
        text_x = 185

    p.setFont("Helvetica-Bold", 20)
    p.drawString(text_x, height - 70, "TECH_INSTITUTE")
    p.setFont("Helvetica", 11)
    p.drawString(text_x, height - 95, "Official Academic Results Transcript")
    p.line(50, height - 155, width - 50, height - 155)

    student_name = request.user.get_full_name() or request.user.username
    adm_no = request.user.admission_number or f"TI-{request.user.id:04d}"

    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, height - 180, f"Student Name: {student_name}")
    p.drawString(50, height - 200, f"Admission No: {adm_no}")

    y = height - 245
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y, "Course")
    p.drawString(280, y, "CAT (30)")
    p.drawString(350, y, "Exam (70)")
    p.drawString(430, y, "Total")
    p.drawString(490, y, "Grade")
    p.line(50, y - 6, width - 50, y - 6)
    y -= 26

    p.setFont("Helvetica", 11)
    for res in results:
        p.drawString(50, y, f"{res.course.code} - {res.course.title[:28]}")
        p.drawString(285, y, str(res.cat_score))
        p.drawString(355, y, str(res.exam_score))
        p.drawString(435, y, str(res.total_score))
        p.setFont("Helvetica-Bold", 11)
        p.drawString(495, y, res.grade)
        p.setFont("Helvetica", 11)
        y -= 22

    if not results:
        p.drawString(50, y, "No published exam results on record.")

    from portal.pdf_utils import draw_official_stamp
    draw_official_stamp(p, x=430, y=110)
    p.showPage()
    p.save()
    return response


@login_required
def instructor_dashboard(request):
    if request.user.role != 'instructor' and not request.user.is_staff:
        messages.error(request, "Access denied. Instructor portal only.")
        return redirect('portal:dashboard')

    if request.user.is_staff or request.user.role == 'admin':
        taught_courses = Course.objects.all()
    else:
        taught_courses = Course.objects.filter(instructor=request.user)

    enrollments = Enrollment.objects.filter(course__in=taught_courses, status='approved').select_related('student', 'course')
    submissions = Submission.objects.filter(assignment__course__in=taught_courses).select_related('student', 'assignment', 'assignment__course').order_by('-submitted_at')
    results = ExamResult.objects.filter(course__in=taught_courses).select_related('student', 'course')
    schedules = ClassSchedule.objects.filter(course__in=taught_courses).select_related('course')
    announcements = Announcement.objects.filter(
        Q(course__isnull=True) | Q(course__in=taught_courses),
        audience__in=['all', 'instructors']
    ).select_related('course', 'posted_by')[:5]

    material_form = StudyMaterialForm()
    material_form.fields['course'].queryset = taught_courses

    assignment_form = AssignmentForm()
    assignment_form.fields['course'].queryset = taught_courses

    notice_form = AnnouncementForm()
    notice_form.fields['course'].queryset = taught_courses

    result_form = ExamResultForm()
    result_form.fields['course'].queryset = taught_courses
    result_form.fields['student'].queryset = User.objects.filter(
        id__in=enrollments.values_list('student_id', flat=True)
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'upload_material':
            material_form = StudyMaterialForm(request.POST, request.FILES)
            if material_form.is_valid():
                material_form.save()
                messages.success(request, "Study material uploaded successfully!")
                return redirect('portal:instructor_dashboard')

        elif action == 'create_assignment':
            assignment_form = AssignmentForm(request.POST)
            if assignment_form.is_valid():
                assignment_form.save()
                messages.success(request, "Assignment posted to students!")
                return redirect('portal:instructor_dashboard')

        elif action == 'post_notice':
            notice_form = AnnouncementForm(request.POST)
            if notice_form.is_valid():
                notice = notice_form.save(commit=False)
                notice.posted_by = request.user
                notice.save()
                messages.success(request, "Announcement posted to the noticeboard!")
                return redirect('portal:instructor_dashboard')

        elif action == 'enter_marks':
            student_id = request.POST.get('student')
            course_id = request.POST.get('course')
            cat_score = request.POST.get('cat_score')
            exam_score = request.POST.get('exam_score')

            ExamResult.objects.update_or_create(
                student_id=student_id,
                course_id=course_id,
                defaults={'cat_score': cat_score, 'exam_score': exam_score}
            )
            messages.success(request, "Exam marks saved and published!")
            return redirect('portal:instructor_dashboard')

    return render(request, 'portal/instructor_dashboard.html', {
        'taught_courses': taught_courses,
        'enrollments': enrollments,
        'submissions': submissions,
        'results': results,
        'schedules': schedules,
        'announcements': announcements,
        'material_form': material_form,
        'assignment_form': assignment_form,
        'notice_form': notice_form,
        'result_form': result_form,
    })


@login_required
def grade_submission(request, submission_id):
    if request.user.role != 'instructor' and not request.user.is_staff:
        return redirect('portal:dashboard')

    if request.user.is_staff or request.user.role == 'admin':
        submission = get_object_or_404(Submission, id=submission_id)
    else:
        submission = get_object_or_404(Submission, id=submission_id, assignment__course__instructor=request.user)

    if request.method == 'POST':
        form = GradeSubmissionForm(request.POST, instance=submission)
        if form.is_valid():
            form.save()
            messages.success(request, f"Graded {submission.student.username}'s submission.")
            return redirect('portal:instructor_dashboard')
    else:
        form = GradeSubmissionForm(instance=submission)

    return render(request, 'portal/grade_submission.html', {
        'submission': submission,
        'form': form,
    })
@login_required
def admin_dashboard(request):
    if request.user.role != 'admin' and not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('portal:dashboard')

    total_students = User.objects.filter(role='student').count()
    total_instructors = User.objects.filter(role='instructor').count()
    total_courses = Course.objects.count()
    total_revenue = Transaction.objects.filter(status='Completed').aggregate(total=Sum('amount'))['total'] or 0

    pending_enrollments = Enrollment.objects.filter(status='pending').select_related('student', 'course').order_by('-enrolled_at')
    all_enrollments = Enrollment.objects.exclude(status='pending').select_related('student', 'course').order_by('-enrolled_at')[:10]
    recent_transactions = Transaction.objects.select_related('student', 'enrollment__course').order_by('-created_at')[:10]
    schedules = ClassSchedule.objects.select_related('course').all()
    announcements = Announcement.objects.select_related('course', 'posted_by')[:8]
    users = User.objects.all().order_by('-date_joined')
    inquiries = ContactMessage.objects.all().order_by('is_resolved', '-submitted_at')[:15]
    all_courses = Course.objects.select_related('instructor').all().order_by('code')
    instructors = User.objects.filter(role='instructor').order_by('first_name', 'username')
    team_members = TeamMember.objects.all()

    course_form = CourseForm()
    schedule_form = ClassScheduleForm()
    notice_form = AnnouncementForm()
    team_form = TeamMemberForm()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_instructor':
            uname = request.POST.get('username', '').strip()
            pwd = request.POST.get('password', '').strip()
            if not uname or not pwd:
                messages.error(request, 'Username and password are required.')
            elif User.objects.filter(username=uname).exists():
                messages.error(request, 'That username already exists.')
            else:
                inst = User.objects.create_user(
                    username=uname,
                    email=request.POST.get('email', '').strip(),
                    password=pwd,
                    first_name=request.POST.get('first_name', '').strip(),
                    last_name=request.POST.get('last_name', '').strip()
                )
                User.objects.filter(id=inst.id).update(
                    role='instructor',
                    admission_number=None,
                    phone_number=request.POST.get('phone_number', '').strip()
                )
                messages.success(request, f'Instructor {uname} created and ready.')
                return redirect('portal:admin_dashboard')

        if action == 'add_course':
            course_form = CourseForm(request.POST)
            if course_form.is_valid():
                course = course_form.save()
                messages.success(request, f"Course {course.code} - {course.title} added to catalog!")
                return redirect('portal:admin_dashboard')

        elif action == 'add_schedule':
            schedule_form = ClassScheduleForm(request.POST)
            if schedule_form.is_valid():
                sched = schedule_form.save()
                messages.success(
                    request,
                    f"Scheduled {sched.course.code} on {sched.day_of_week} ({sched.start_time.strftime('%H:%M')} - {sched.end_time.strftime('%H:%M')})."
                )
                return redirect('portal:admin_dashboard')

        elif action == 'post_notice':
            notice_form = AnnouncementForm(request.POST)
            if notice_form.is_valid():
                notice = notice_form.save(commit=False)
                notice.posted_by = request.user
                notice.save()
                messages.success(request, "Announcement published to the noticeboard!")
                return redirect('portal:admin_dashboard')

        elif action == 'add_team':
            team_form = TeamMemberForm(request.POST, request.FILES)
            if team_form.is_valid():
                member = team_form.save()
                messages.success(request, f"Added {member.full_name} to the Meet the Team section!")
                return redirect('portal:admin_dashboard')

    return render(request, 'portal/admin_dashboard.html', {
        'total_students': total_students,
        'total_instructors': total_instructors,
        'total_courses': total_courses,
        'total_revenue': total_revenue,
        'pending_enrollments': pending_enrollments,
        'all_enrollments': all_enrollments,
        'recent_transactions': recent_transactions,
        'schedules': schedules,
        'announcements': announcements,
        'users': users,
        'inquiries': inquiries,
        'all_courses': all_courses,
        'instructors': instructors,
        'team_members': team_members,
        'course_form': course_form,
        'schedule_form': schedule_form,
        'notice_form': notice_form,
        'team_form': team_form,
    })


@login_required
def manage_enrollment(request, enrollment_id, decision):
    if request.user.role != 'admin' and not request.user.is_staff:
        return redirect('portal:dashboard')

    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    if decision == 'approve':
        enrollment.status = 'approved'
        enrollment.save()

        student = enrollment.student
        if not student.admission_number:
            student.admission_number = f"TI-2026-{student.id:04d}"
            student.save()

        messages.success(request, f"Approved {student.username} for {enrollment.course.code} (Adm No: {student.admission_number}).")
    elif decision == 'reject':
        enrollment.status = 'rejected'
        enrollment.save()
        messages.info(request, f"Rejected application for {enrollment.student.username}.")

    return redirect('portal:admin_dashboard')


@login_required
def resolve_inquiry(request, inquiry_id):
    if request.user.role != 'admin' and not request.user.is_staff:
        return redirect('portal:dashboard')

    inquiry = get_object_or_404(ContactMessage, id=inquiry_id)
    inquiry.is_resolved = True
    inquiry.save()
    messages.success(request, f"Marked inquiry from {inquiry.full_name} as resolved.")
    return redirect('portal:admin_dashboard')


@login_required
def update_user_role(request, user_id):
    if request.user.role != 'admin' and not request.user.is_staff:
        return redirect('portal:dashboard')

    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        new_role = request.POST.get('role')

        if new_role in ['student', 'instructor', 'admin']:
            target_user.role = new_role
            target_user.is_staff = (new_role == 'admin')
            target_user.save()
            messages.success(request, f"Updated {target_user.username}'s role to {target_user.get_role_display()}.")

    return redirect('portal:admin_dashboard')


@login_required
def delete_user(request, user_id):
    if request.user.role != 'admin' and not request.user.is_staff:
        return redirect('portal:dashboard')

    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        if target_user == request.user or target_user.is_superuser:
            messages.error(request, "You cannot delete your own account or a system superuser.")
        else:
            username = target_user.username
            target_user.delete()
            messages.info(request, f"User account '{username}' has been permanently deleted.")

    return redirect('portal:admin_dashboard')


@login_required
def assign_course_instructor(request, course_id):
    if request.user.role != 'admin' and not request.user.is_staff:
        return redirect('portal:dashboard')

    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        instructor_id = request.POST.get('instructor_id')

        if instructor_id:
            instructor = get_object_or_404(User, id=instructor_id, role='instructor')
            course.instructor = instructor
            course.save()
            messages.success(request, f"Assigned {instructor.get_full_name() or instructor.username} to {course.code}.")
        else:
            course.instructor = None
            course.save()
            messages.info(request, f"Unassigned instructor from {course.code}.")

    return redirect('portal:admin_dashboard')


@login_required
def delete_team_member(request, member_id):
    if request.user.role != 'admin' and not request.user.is_staff:
        return redirect('portal:dashboard')

    member = get_object_or_404(TeamMember, id=member_id)
    member.delete()
    messages.info(request, f"Removed {member.full_name} from the team list.")
    return redirect('portal:admin_dashboard')


@login_required
def delete_announcement(request, announcement_id):
    if request.user.role not in ['admin', 'instructor'] and not request.user.is_staff:
        return redirect('portal:dashboard')

    if request.method == 'POST':
        notice = get_object_or_404(Announcement, id=announcement_id)
        if request.user.role == 'admin' or request.user.is_staff or notice.posted_by == request.user:
            notice.delete()
            messages.info(request, "Announcement removed from the noticeboard.")
        else:
            messages.error(request, "You can only delete announcements you posted.")

    if request.user.role == 'instructor' and not request.user.is_staff:
        return redirect('portal:instructor_dashboard')
    return redirect('portal:admin_dashboard')

@login_required
def admin_dashboard(request):
    if request.user.role != 'admin' and not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('portal:dashboard')

    total_students = User.objects.filter(role='student').count()
    total_instructors = User.objects.filter(role='instructor').count()
    total_courses = Course.objects.count()
    total_revenue = Transaction.objects.filter(status='Completed').aggregate(total=Sum('amount'))['total'] or 0

    pending_enrollments = Enrollment.objects.filter(status='pending').select_related('student', 'course').order_by('-enrolled_at')
    all_enrollments = Enrollment.objects.exclude(status='pending').select_related('student', 'course').order_by('-enrolled_at')[:10]
    recent_transactions = Transaction.objects.select_related('student', 'enrollment__course').order_by('-created_at')[:10]
    schedules = ClassSchedule.objects.select_related('course').all()
    announcements = Announcement.objects.select_related('course', 'posted_by')[:8]
    users = User.objects.all().order_by('-date_joined')
    inquiries = ContactMessage.objects.all().order_by('is_resolved', '-submitted_at')[:15]
    all_courses = Course.objects.select_related('instructor').all().order_by('code')
    instructors = User.objects.filter(role='instructor').order_by('first_name', 'username')
    team_members = TeamMember.objects.all()

    course_form = CourseForm()
    schedule_form = ClassScheduleForm()
    notice_form = AnnouncementForm()
    team_form = TeamMemberForm()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_instructor':
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '')
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            phone = request.POST.get('phone_number', '').strip()
            from django.contrib.auth import get_user_model
            InstructorUser = get_user_model()
            if not username or not password:
                messages.error(request, "Username and Temporary Password are required.")
            elif InstructorUser.objects.filter(username=username).exists():
                messages.error(request, f"Username {username} already exists.")
            else:
                user = InstructorUser.objects.create_user(username=username, email=email, password=password, first_name=first_name, last_name=last_name)
                if hasattr(user, 'role'):
                    user.role = 'instructor'
                if hasattr(user, 'phone_number'):
                    user.phone_number = phone
                user.is_staff = False
                user.save()
                messages.success(request, f"Instructor {username} created successfully! They can now log in.")
            return redirect('portal:admin_dashboard')
        if action == 'add_course':
            course_form = CourseForm(request.POST)
            if course_form.is_valid():
                course = course_form.save()
                messages.success(request, f"Course {course.code} - {course.title} added to catalog!")
                return redirect('portal:admin_dashboard')

        elif action == 'add_schedule':
            schedule_form = ClassScheduleForm(request.POST)
            if schedule_form.is_valid():
                sched = schedule_form.save()
                messages.success(
                    request,
                    f"Scheduled {sched.course.code} on {sched.day_of_week} ({sched.start_time.strftime('%H:%M')} - {sched.end_time.strftime('%H:%M')})."
                )
                return redirect('portal:admin_dashboard')

        elif action == 'post_notice':
            notice_form = AnnouncementForm(request.POST)
            if notice_form.is_valid():
                notice = notice_form.save(commit=False)
                notice.posted_by = request.user
                notice.save()
                messages.success(request, "Announcement published to the noticeboard!")
                return redirect('portal:admin_dashboard')

        elif action == 'add_team':
            team_form = TeamMemberForm(request.POST, request.FILES)
            if team_form.is_valid():
                member = team_form.save()
                messages.success(request, f"Added {member.full_name} to the Meet the Team section!")
                return redirect('portal:admin_dashboard')

    return render(request, 'portal/admin_dashboard.html', {
        'total_students': total_students,
        'total_instructors': total_instructors,
        'total_courses': total_courses,
        'total_revenue': total_revenue,
        'pending_enrollments': pending_enrollments,
        'all_enrollments': all_enrollments,
        'recent_transactions': recent_transactions,
        'schedules': schedules,
        'announcements': announcements,
        'users': users,
        'inquiries': inquiries,
        'all_courses': all_courses,
        'instructors': instructors,
        'team_members': team_members,
        'course_form': course_form,
        'schedule_form': schedule_form,
        'notice_form': notice_form,
        'team_form': team_form,
    })


@login_required
def manage_enrollment(request, enrollment_id, decision):
    if request.user.role != 'admin' and not request.user.is_staff:
        return redirect('portal:dashboard')

    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    if decision == 'approve':
        enrollment.status = 'approved'
        enrollment.save()

        student = enrollment.student
        if not student.admission_number:
            student.admission_number = f"TI-2026-{student.id:04d}"
            student.save()

        messages.success(request, f"Approved {student.username} for {enrollment.course.code} (Adm No: {student.admission_number}).")
    elif decision == 'reject':
        enrollment.status = 'rejected'
        enrollment.save()
        messages.info(request, f"Rejected application for {enrollment.student.username}.")

    return redirect('portal:admin_dashboard')


@login_required
def resolve_inquiry(request, inquiry_id):
    if request.user.role != 'admin' and not request.user.is_staff:
        return redirect('portal:dashboard')

    inquiry = get_object_or_404(ContactMessage, id=inquiry_id)
    inquiry.is_resolved = True
    inquiry.save()
    messages.success(request, f"Marked inquiry from {inquiry.full_name} as resolved.")
    return redirect('portal:admin_dashboard')


@login_required
def update_user_role(request, user_id):
    if request.user.role != 'admin' and not request.user.is_staff:
        return redirect('portal:dashboard')

    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        new_role = request.POST.get('role')

        if new_role in ['student', 'instructor', 'admin']:
            target_user.role = new_role
            target_user.is_staff = (new_role == 'admin')
            target_user.save()
            messages.success(request, f"Updated {target_user.username}'s role to {target_user.get_role_display()}.")

    return redirect('portal:admin_dashboard')


@login_required
def delete_user(request, user_id):
    if request.user.role != 'admin' and not request.user.is_staff:
        return redirect('portal:dashboard')

    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        if target_user == request.user or target_user.is_superuser:
            messages.error(request, "You cannot delete your own account or a system superuser.")
        else:
            username = target_user.username
            target_user.delete()
            messages.info(request, f"User account '{username}' has been permanently deleted.")

    return redirect('portal:admin_dashboard')


@login_required
def assign_course_instructor(request, course_id):
    if request.user.role != 'admin' and not request.user.is_staff:
        return redirect('portal:dashboard')

    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        instructor_id = request.POST.get('instructor_id')

        if instructor_id:
            instructor = get_object_or_404(User, id=instructor_id, role='instructor')
            course.instructor = instructor
            course.save()
            messages.success(request, f"Assigned {instructor.get_full_name() or instructor.username} to {course.code}.")
        else:
            course.instructor = None
            course.save()
            messages.info(request, f"Unassigned instructor from {course.code}.")

    return redirect('portal:admin_dashboard')


@login_required
def delete_team_member(request, member_id):
    if request.user.role != 'admin' and not request.user.is_staff:
        return redirect('portal:dashboard')

    member = get_object_or_404(TeamMember, id=member_id)
    member.delete()
    messages.info(request, f"Removed {member.full_name} from the team list.")
    return redirect('portal:admin_dashboard')


@login_required
def delete_announcement(request, announcement_id):
    if request.user.role not in ['admin', 'instructor'] and not request.user.is_staff:
        return redirect('portal:dashboard')

    if request.method == 'POST':
        notice = get_object_or_404(Announcement, id=announcement_id)
        if request.user.role == 'admin' or request.user.is_staff or notice.posted_by == request.user:
            notice.delete()
            messages.info(request, "Announcement removed from the noticeboard.")
        else:
            messages.error(request, "You can only delete announcements you posted.")

    if request.user.role == 'instructor' and not request.user.is_staff:
        return redirect('portal:instructor_dashboard')
    return redirect('portal:admin_dashboard')
@login_required
def delete_team_member(request, member_id):
    if request.user.role != 'admin' and not request.user.is_staff:
        return redirect('portal:dashboard')

    member = get_object_or_404(TeamMember, id=member_id)
    member.delete()
    messages.info(request, f"Removed {member.full_name} from the team list.")
    return redirect('portal:admin_dashboard')

# ===== ADMIN ONLY - USER MANAGEMENT =====
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import get_user_model

def is_admin_user(user):
    return user.is_authenticated and (user.is_superuser or getattr(user, 'role', '') == 'admin')

@user_passes_test(is_admin_user)
def admin_users(request):
    User = get_user_model()
    # ?role=instructor or ?role=student to filter, ?q=search
    role = request.GET.get('role', '')
    q = request.GET.get('q', '')
    users = User.objects.all().order_by('-date_joined')
    if role:
        users = users.filter(role=role)
    if q:
        users = users.filter(username__icontains=q) | users.filter(email__icontains=q) | users.filter(first_name__icontains=q)
    return render(request, 'portal/admin_users.html', {'users': users, 'role_filter': role, 'q': q})

@user_passes_test(is_admin_user)
def admin_create_instructor(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('portal:admin_create_instructor')
        user = User.objects.create_user(username=username, email=email, password=password, first_name=first_name, last_name=last_name)
        user.role = 'instructor'
        user.is_staff = False  # NOT staff, so he doesn't get mistaken for admin
        user.save()
        messages.success(request, f"Instructor {username} created.")
        return redirect('portal:admin_users')
    return render(request, 'portal/admin_create_instructor.html')

@user_passes_test(is_admin_user)
def admin_delete_user(request, user_id):
    User = get_user_model()
    user_to_delete = get_object_or_404(User, id=user_id)
    # Safety: Admin cannot delete himself or another superuser
    if user_to_delete == request.user:
        messages.error(request, "You cannot delete yourself.")
        return redirect('portal:admin_users')
    if user_to_delete.is_superuser:
        messages.error(request, "Cannot delete a superuser.")
        return redirect('portal:admin_users')
    if request.method == 'POST':
        username = user_to_delete.username
        role = getattr(user_to_delete, 'role', '')
        # This deletes User + all related records (courses, enrollments, etc.) via CASCADE
        user_to_delete.delete()
        messages.success(request, f"{role.capitalize()} {username} and all their records deleted.")
        return redirect('portal:admin_users')
    return render(request, 'portal/admin_confirm_delete.html', {'delete_user': user_to_delete})

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

def is_admin_user(user):
    return user.is_authenticated and (user.is_superuser or getattr(user, 'role', '') == 'admin')

@user_passes_test(is_admin_user)
def admin_users(request):
    User = get_user_model()
    role = request.GET.get('role', '')
    q = request.GET.get('q', '')
    users = User.objects.all().order_by('-date_joined')
    if role:
        users = users.filter(role=role)
    if q:
        users = users.filter(username__icontains=q)
    return render(request, 'portal/admin_users.html', {'users': users, 'role_filter': role, 'q': q})

@user_passes_test(is_admin_user)
def admin_create_instructor(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('portal:admin_create_instructor')
        user = User.objects.create_user(username=username, email=email, password=password, first_name=first_name, last_name=last_name)
        user.role = 'instructor'
        user.is_staff = False
        user.save()
        messages.success(request, f"Instructor {username} created.")
        return redirect('portal:admin_users')
    return render(request, 'portal/admin_create_instructor.html')

@user_passes_test(is_admin_user)
def admin_delete_user(request, user_id):
    User = get_user_model()
    user_to_delete = get_object_or_404(User, id=user_id)
    if user_to_delete == request.user:
        messages.error(request, "You cannot delete yourself.")
        return redirect('portal:admin_users')
    if user_to_delete.is_superuser:
        messages.error(request, "Cannot delete a superuser.")
        return redirect('portal:admin_users')
    if request.method == 'POST':
        username = user_to_delete.username
        role = getattr(user_to_delete, 'role', '')
        user_to_delete.delete()
        messages.success(request, f"{role} {username} deleted.")
        return redirect('portal:admin_users')
    return render(request, 'portal/admin_confirm_delete.html', {'delete_user': user_to_delete})
