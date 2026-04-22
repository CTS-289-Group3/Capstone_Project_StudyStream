# accounts/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Auth
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
    template_name='accounts/password_reset.html',
    email_template_name='accounts/password_reset_email.txt',
    subject_template_name='accounts/password_reset_subject.txt',
    extra_email_context={
        'domain': 'opulent-garbanzo-x5xw7g4qjxvjcvvj6-8000.app.github.dev',
        'protocol': 'https',
    }
    ), name='password_reset'),

    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html',
    ), name='password_reset_done'),

    path('password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
    ), name='password_reset_confirm'),

    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html',
    ), name='password_reset_complete'),
    path('settings/', views.settings_view, name='settings'),

    # Semesters
    path('api/semesters/', views.semester_list_json, name='semester_list_json'),
    path('api/semesters/create/', views.semester_create, name='semester_create'),
    path('api/semesters/<int:pk>/edit/', views.semester_edit, name='semester_edit'),
    path('api/semesters/<int:pk>/delete/', views.semester_delete, name='semester_delete'),

    # Courses
    path('api/courses/', views.course_list_json, name='course_list_json'),
    path('api/courses/create/', views.course_create, name='course_create'),
    path('api/courses/<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('api/courses/<int:pk>/delete/', views.course_delete, name='course_delete'),

    # Tags
    path('api/tags/', views.tag_list_json, name='tag_list_json'),
    path('api/tags/create/', views.tag_create, name='tag_create'),
    path('api/tags/<int:pk>/delete/', views.tag_delete, name='tag_delete'),

    # Assignments
    path('api/assignments/', views.assignment_list_json, name='assignment_list_json'),
    path('api/assignments/create/', views.assignment_create, name='assignment_create'),
    path('api/assignments/<int:pk>/edit/', views.assignment_edit, name='assignment_edit'),
    path('api/assignments/<int:pk>/delete/', views.assignment_delete, name='assignment_delete'),
    path('api/assignments/<int:pk>/status/', views.assignment_status_update, name='assignment_status_update'),

    # Subtasks
    path('api/assignments/<int:assignment_pk>/subtasks/', views.subtask_list_json, name='subtask_list_json'),
    path('api/assignments/<int:assignment_pk>/subtasks/create/', views.subtask_create, name='subtask_create'),
    path('api/subtasks/<int:pk>/edit/', views.subtask_edit, name='subtask_edit'),
    path('api/subtasks/<int:pk>/toggle/', views.subtask_toggle, name='subtask_toggle'),
    path('api/subtasks/<int:pk>/delete/', views.subtask_delete, name='subtask_delete'),
]