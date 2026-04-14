# home/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/add/personal-event/', views.add_personal_event, name='add_personal_event'),
    path('dashboard/add/work-shift/', views.add_work_shift, name='add_work_shift'),
    path('dashboard/recurring-shifts/', views.recurring_shift_list, name='recurring_shift_list'),
    path('dashboard/recurring-shifts/add/', views.add_recurring_shift, name='add_recurring_shift'),
    path('dashboard/recurring-shifts/<int:shift_id>/edit/', views.edit_recurring_shift, name='edit_recurring_shift'),
    path('dashboard/recurring-shifts/<int:shift_id>/delete/', views.delete_recurring_shift, name='delete_recurring_shift'),
    path('dashboard/recurring-personal-events/', views.recurring_personal_event_list, name='recurring_personal_event_list'),
    path('dashboard/recurring-personal-events/add/', views.add_recurring_personal_event, name='add_recurring_personal_event'),
    path('dashboard/recurring-personal-events/<int:event_id>/edit/', views.edit_recurring_personal_event, name='edit_recurring_personal_event'),
    path('dashboard/recurring-personal-events/<int:event_id>/delete/', views.delete_recurring_personal_event, name='delete_recurring_personal_event'),
    path('dashboard/recurring-locations/', views.recurring_location_list, name='recurring_location_list'),
    path('dashboard/recurring-locations/add/', views.add_recurring_location, name='add_recurring_location'),
    path('dashboard/recurring-locations/<int:location_id>/edit/', views.edit_recurring_location, name='edit_recurring_location'),
    path('dashboard/recurring-locations/<int:location_id>/delete/', views.delete_recurring_location, name='delete_recurring_location'),
    path('dashboard/recurring-job-titles/', views.recurring_job_title_list, name='recurring_job_title_list'),
    path('dashboard/recurring-job-titles/add/', views.add_recurring_job_title, name='add_recurring_job_title'),
    path('dashboard/recurring-job-titles/<int:title_id>/edit/', views.edit_recurring_job_title, name='edit_recurring_job_title'),
    path('dashboard/recurring-job-titles/<int:title_id>/delete/', views.delete_recurring_job_title, name='delete_recurring_job_title'),
    
    # API endpoints for personal event editing
    path('api/personal-events/<int:event_id>/edit/', views.personal_event_edit, name='personal_event_edit'),
    path('api/personal-events/<int:event_id>/delete/', views.personal_event_delete, name='personal_event_delete'),
    
    # API endpoints for work shift editing
    path('api/work-shifts/<int:shift_id>/edit/', views.work_shift_edit, name='work_shift_edit'),
    path('api/work-shifts/<int:shift_id>/delete/', views.work_shift_delete, name='work_shift_delete'),
]