from django.contrib import admin
from .models import GoogleConnection

@admin.register(GoogleConnection)
class GoogleConnectionAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'google_user_id', 'is_active', 'created_at', 'last_synced_at')
    list_filter = ('is_active',)
    search_fields = ('user__email', 'email', 'google_user_id')
    readonly_fields = ('access_token_encrypted', 'refresh_token_encrypted', 'created_at', 'updated_at')
