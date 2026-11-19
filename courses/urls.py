from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.about_us, name='about_us'),
    path('contact/', views.contact_us, name='contact_us'),
    path('catalog/', views.course_list, name='course_list'),
    path('catalog/<int:course_id>/', views.course_detail, name='course_detail'),
]
