from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('tags/', include('tags.urls')),
    path('users/', include('users.urls')),
    path('tweets/', include('tweets.urls')), 
    path('', RedirectView.as_view(pattern_name='tweets:all_tweets', permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
