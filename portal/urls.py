from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    path('dashboard/', views.student_dashboard, name='dashboard'),
    path('assignment/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('transcript/download/', views.download_transcript, name='download_transcript'),
    path('instructor/', views.instructor_dashboard, name='instructor_dashboard'),
    path('submission/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('enrollment/<int:enrollment_id>/<str:decision>/', views.manage_enrollment, name='manage_enrollment'),
    path('inquiry/<int:inquiry_id>/resolve/', views.resolve_inquiry, name='resolve_inquiry'),
    path('user/<int:user_id>/role/', views.update_user_role, name='update_user_role'),
    path('user/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('course/<int:course_id>/assign-instructor/', views.assign_course_instructor, name='assign_course_instructor'),
    path('team/<int:member_id>/delete/', views.delete_team_member, name='delete_team_member'),
    path('announcement/<int:announcement_id>/delete/', views.delete_announcement, name='delete_announcement'),
    path('team/<int:member_id>/delete/', views.delete_team_member, name='delete_team_member'),

]
