from django.contrib import admin
from .models import Semester, Course, Assignment, AssignmentSubtask, TimeBlock, Tag

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'start_date', 'end_date', 'is_active']
    list_filter  = ['is_active', 'user']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_code', 'course_name', 'semester', 'user', 'professor_name']
    list_filter  = ['semester', 'user']

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_hex', 'user']
    list_filter  = ['user']

class SubtaskInline(admin.TabularInline):
    model = AssignmentSubtask
    extra = 0

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display  = ['title', 'course', 'user', 'due_date', 'status', 'priority']
    list_filter   = ['status', 'priority', 'course__semester', 'user']
    inlines       = [SubtaskInline]
    filter_horizontal = ['tags']

@admin.register(AssignmentSubtask)
class SubtaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'assignment', 'status', 'sequence_order']

@admin.register(TimeBlock)
class TimeBlockAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'start_time', 'end_time', 'status']