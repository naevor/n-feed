from django.urls import path

from . import views

app_name = 'tags'

urlpatterns = [
    path('<str:name>/', views.tag_detail, name='tag_detail'),
]
