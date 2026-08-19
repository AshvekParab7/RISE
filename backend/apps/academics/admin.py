from django.contrib import admin
from .models import CollegeClass, Exam, Semester, Subject, Syllabus, Topic

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'student', 'year', 'semester_number', 'is_current')
    list_filter = ('is_current', 'year')
    search_fields = ('name', 'student__email')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'semester', 'difficulty', 'mastery_percentage', 'priority_score', 'exam_date')
    list_filter = ('difficulty', 'semester')
    search_fields = ('name', 'code')
    ordering = ('exam_date', 'name')

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'unit_name', 'status', 'mastery_percentage', 'order')
    list_filter = ('status', 'subject')
    search_fields = ('name', 'unit_name')
    ordering = ('subject', 'unit_name', 'order')

@admin.register(Syllabus)
class SyllabusAdmin(admin.ModelAdmin):
    list_display = ('title', 'semester', 'processing_status', 'uploaded_at')
    list_filter = ('processing_status', 'semester')
    search_fields = ('title',)

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'exam_date', 'start_time', 'source')
    list_filter = ('source', 'exam_date')
    search_fields = ('title', 'subject__name')

@admin.register(CollegeClass)
class CollegeClassAdmin(admin.ModelAdmin):
    list_display = ('subject', 'semester', 'day_of_week', 'start_time', 'end_time', 'room')
    list_filter = ('day_of_week', 'semester')
    search_fields = ('subject__name', 'instructor', 'room')
