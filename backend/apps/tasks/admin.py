from django.contrib import admin
from .models import StudySession, Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'subject', 'deadline', 'priority', 'source', 'status')
    list_filter = ('priority', 'source', 'status')
    search_fields = ('title', 'description', 'student__email', 'subject__name')
    ordering = ('status', 'deadline')

@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'topic', 'planned_minutes', 'actual_minutes', 'status', 'created_at')
    list_filter = ('status', 'subject')
    search_fields = ('student__email', 'subject__name', 'topic__name')
    ordering = ('-created_at',)
