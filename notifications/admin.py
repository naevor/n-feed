from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'actor', 'kind', 'tweet', 'is_read', 'created_at')
    list_filter = ('kind', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'actor__username', 'tweet__content')
    autocomplete_fields = ('recipient', 'actor', 'tweet')
    ordering = ('-created_at',)
