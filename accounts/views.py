from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from admissions.models import Enrollment
from portal.pdf_utils import draw_pdf_header, draw_official_stamp
from .forms import ProfileUpdateForm

User = get_user_model()

def redirect_by_role(user):
    if user.role == 'instructor':
        return redirect('portal:instructor_dashboard')
    if user.is_superuser or user.role == 'admin':
        return redirect('portal:admin_dashboard')
    return redirect('portal:dashboard')

def login_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect_by_role(user)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('accounts:login')

@login_required
def profile_view(request):
    approved_enrollments = Enrollment.objects.filter(student=request.user, status='approved')

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'accounts/profile.html', {
        'form': form,
        'approved_enrollments': approved_enrollments,
    })

@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password has been updated successfully!")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})

@login_required
def download_admission_letter(request, enrollment_id):
    enrollment = Enrollment.objects.filter(
        id=enrollment_id,
        student=request.user,
        status='approved'
    ).first()

    if not enrollment:
        messages.error(request, "Admission letter is only available for approved courses.")
        return redirect('accounts:profile')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Admission_Letter_{enrollment.course.code}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    draw_pdf_header(p, width, height, "Office of the Registrar - Admissions Department")

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height - 185, "OFFICIAL LETTER OF ADMISSION")

    y = height - 220
    student_name = request.user.get_full_name() or request.user.username
    adm_no = request.user.admission_number or f"TI-{request.user.id:04d}"

    lines = [
        f"Student Name: {student_name}",
        f"Admission Number: {adm_no}",
        f"Phone Number: {request.user.phone_number or 'N/A'}",
        "",
        f"Dear {student_name},",
        "",
        "We are pleased to inform you that your application to join TECH_INSTITUTE has been",
        "approved. You have been admitted into the following academic program:",
        "",
        f"Program / Course: {enrollment.course.code} - {enrollment.course.title}",
        f"Duration: {enrollment.course.duration_months} Months",
        f"Total Tuition Fee: KES {enrollment.course.tuition_fee:,.2f}",
        f"Fee Paid to Date: KES {enrollment.fee_paid:,.2f}",
        "",
        "Please retain this letter for student ID issuance and portal verification.",
        "",
        "Sincerely,",
        "Registrar, TECH_INSTITUTE"
    ]

    for line in lines:
        if line.startswith(("Student Name:", "Admission Number:", "Program / Course:", "Total Tuition", "Fee Paid")):
            p.setFont("Helvetica-Bold", 11)
        else:
            p.setFont("Helvetica", 11)
        p.drawString(50, y, line)
        y -= 22

    draw_official_stamp(p, x=430, y=y + 25)

    p.showPage()
    p.save()
    return response

def register_view(request):
    from .forms import StudentRegistrationForm
    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        first_name = (request.POST.get('first_name') or '').strip()
        last_name = (request.POST.get('last_name') or '').strip()
        email = (request.POST.get('email') or '').strip()
        phone = (request.POST.get('phone_number') or '').strip()
        password1 = request.POST.get('password1') or ''
        password2 = request.POST.get('password2') or ''

        if not username:
            messages.error(request, "Username is required. Please enter a username.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "That username is already taken. Try another.")
        elif email and User.objects.filter(email=email).exists():
            messages.error(request, "That email is already registered. Try logging in.")
        elif not password1 or password1 != password2:
            messages.error(request, "Passwords do not match.")
        elif len(password1) < 8:
            messages.error(request, "Password must be at least 8 characters.")
        else:
            if phone.startswith('07') or phone.startswith('01'):
                phone = '254' + phone[1:]
            elif phone.startswith('+254'):
                phone = phone[1:]
            user = User.objects.create_user(
                username=username, email=email, password=password1,
                first_name=first_name, last_name=last_name,
            )
            if hasattr(user, 'phone_number'):
                user.phone_number = phone
            if hasattr(user, 'role'):
                user.role = 'student'
            user.save()
            login(request, user)
            messages.success(request, f"Welcome, {username}!")
            return redirect_by_role(user)
        form = StudentRegistrationForm(request.POST)
        return render(request, 'accounts/register.html', {'form': form})

    form = StudentRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})