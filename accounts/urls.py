# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

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
    path('api/subtasks/<int:pk>/toggle/', views.subtask_toggle, name='subtask_toggle'),
    path('api/subtasks/<int:pk>/delete/', views.subtask_delete, name='subtask_delete'),
]