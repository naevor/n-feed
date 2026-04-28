from django.contrib import admin
from .models import Comment, Tweet

@admin.register(Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'created_at')
    search_fields = ('content', 'user__username')
    list_filter = ('created_at',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'tweet', 'created_at')
    search_fields = ('content', 'user__username', 'tweet__content')
