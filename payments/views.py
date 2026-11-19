import json
import os
from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from admissions.models import Enrollment
from .models import Transaction
from .mpesa import initiate_stk_push


@login_required
def pay_fee(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, student=request.user)
    transactions = Transaction.objects.filter(enrollment=enrollment).order_by('-created_at')

    if request.method == 'POST':
        phone = request.POST.get('phone_number', '').strip()
        amount = request.POST.get('amount')

        if phone.startswith('07') or phone.startswith('01'):
            phone = '254' + phone[1:]
        elif phone.startswith('+254'):
            phone = phone[1:]

        callback_url = os.environ.get('MPESA_CALLBACK_URL')
        res = initiate_stk_push(phone, amount, enrollment.course.code, callback_url)

        if res.get('ResponseCode') == '0':
            Transaction.objects.create(
                student=request.user,
                enrollment=enrollment,
                phone_number=phone,
                amount=Decimal(amount),
                checkout_request_id=res['CheckoutRequestID'],
                status='Pending'
            )
            messages.success(request, "STK Push sent! Check your phone and enter your M-Pesa PIN.")
        else:
            error_msg = res.get('errorMessage', 'Failed to initiate M-Pesa prompt.')
            messages.error(request, f"M-Pesa Error: {error_msg}")

        return redirect('payments:pay_fee', enrollment_id=enrollment.id)

    return render(request, 'payments/pay_fee.html', {
        'enrollment': enrollment,
        'transactions': transactions,
    })


@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        stk_callback = data.get('Body', {}).get('stkCallback', {})
        checkout_id = stk_callback.get('CheckoutRequestID')
        result_code = stk_callback.get('ResultCode')

        transaction = Transaction.objects.filter(checkout_request_id=checkout_id).first()
        if transaction and transaction.status == 'Pending':
            if result_code == 0:
                items = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                receipt = next((i['Value'] for i in items if i['Name'] == 'MpesaReceiptNumber'), None)

                transaction.status = 'Completed'
                transaction.mpesa_receipt_number = receipt
                transaction.save()

                enrollment = transaction.enrollment
                enrollment.fee_paid += transaction.amount

                if enrollment.fee_paid >= enrollment.course.tuition_fee:
                    enrollment.status = 'approved'
                elif enrollment.status == 'pending' and enrollment.fee_paid > 0:
                    enrollment.status = 'approved'

                enrollment.save()
            else:
                transaction.status = 'Failed'
                transaction.save()

        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})
    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required
def simulate_success(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, student=request.user, status='Pending')

    transaction.status = 'Completed'
    transaction.mpesa_receipt_number = f"SIM{transaction.id:05d}KE"
    transaction.save()

    enrollment = transaction.enrollment
    enrollment.fee_paid += transaction.amount
    if enrollment.fee_paid > 0 and enrollment.status == 'pending':
        enrollment.status = 'approved'
    enrollment.save()

    messages.success(request, f"Payment of KES {transaction.amount} confirmed! Receipt {transaction.mpesa_receipt_number} generated.")
    return redirect('payments:pay_fee', enrollment_id=enrollment.id)


@login_required
def download_receipt(request, transaction_id):
    transaction = get_object_or_404(
        Transaction,
        id=transaction_id,
        student=request.user,
        status='Completed'
    )
    enrollment = transaction.enrollment

    response = HttpResponse(content_type='application/pdf')
    receipt_no = transaction.mpesa_receipt_number or f"TXN-{transaction.id}"
    response['Content-Disposition'] = f'attachment; filename="Receipt_{receipt_no}.pdf"'

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
    p.drawString(text_x, height - 95, "Official Tuition Fee Payment Receipt")
    p.line(50, height - 155, width - 50, height - 155)

    y = height - 185
    details = [
        ("Receipt Number:", receipt_no),
        ("Date Paid:", transaction.created_at.strftime("%d %b %Y, %I:%M %p")),
        ("Student Name:", request.user.get_full_name() or request.user.username),
        ("Admission Number:", request.user.admission_number or "N/A"),
        ("M-Pesa Phone:", transaction.phone_number),
        ("Course:", f"{enrollment.course.code} - {enrollment.course.title}"),
        ("Enrollment Status:", enrollment.get_status_display()),
    ]

    for label, value in details:
        p.setFont("Helvetica-Bold", 11)
        p.drawString(50, y, label)
        p.setFont("Helvetica", 11)
        p.drawString(200, y, str(value))
        y -= 24

    p.line(50, y - 5, width - 50, y - 5)
    y -= 35

    financials = [
        ("Total Course Tuition:", f"KES {enrollment.course.tuition_fee:,.2f}"),
        ("Amount Paid (This Receipt):", f"KES {transaction.amount:,.2f}"),
        ("Total Paid To Date:", f"KES {enrollment.fee_paid:,.2f}"),
        ("Remaining Fee Balance:", f"KES {enrollment.fee_balance:,.2f}"),
    ]

    for label, value in financials:
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, label)
        p.drawString(250, y, value)
        y -= 26

    p.line(50, y - 10, width - 50, y - 10)
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(50, y - 35, "Thank you for studying at TECH_INSTITUTE. This is a system-generated receipt.")

    p.showPage()
    p.save()
    return response
