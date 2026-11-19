
from django.urls import path
from . import views

app_name = 'admissions'

urlpatterns = [
   path('apply/<int:course_id>/', views.apply_course, name='apply_course'),
    path('my-applications/', views.my_applications, name='my_applications'),
]
