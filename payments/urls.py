from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('pay/<int:enrollment_id>/', views.pay_fee, name='pay_fee'),
    path('callback/', views.mpesa_callback, name='mpesa_callback'),
    path('receipt/<int:transaction_id>/', views.download_receipt, name='download_receipt'),
    path('simulate/<int:transaction_id>/', views.simulate_success, name='simulate_success'),
]
