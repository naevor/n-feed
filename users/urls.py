from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/<str:username>/", views.profile_view, name="profile"),
    path("profile/<str:username>/follow/", views.follow_user_view, name="follow"),
    path("edit-profile/", views.edit_profile_view, name="edit_profile"),
    path("profile/<str:username>/followers/", views.followers_list_view, name="followers_list"),
    path("profile/<str:username>/following/", views.following_list_view, name="following_list"),
    path("delete-account/", views.delete_account_view, name="delete_account"),
]
