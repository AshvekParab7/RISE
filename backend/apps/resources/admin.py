from django.contrib import admin
from .models import Resource

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'subject', 'resource_type', 'source', 'is_ai_ready', 'uploaded_at')
    list_filter = ('resource_type', 'source', 'is_ai_ready')
    search_fields = ('title', 'description', 'student__email', 'subject__name')
    ordering = ('-uploaded_at',)
