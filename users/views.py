from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from tweets.selectors import user_tweets_qs

from . import services
from .forms import EditProfileForm, LoginForm, RegisterForm
from .selectors import get_user_by_username


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("users:profile", username=user.username)
    else:
        form = RegisterForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("users:profile", username=user.username)
    else:
        form = LoginForm()
    return render(request, "users/login.html", {"form": form})


def profile_view(request, username):
    profile_user = get_user_by_username(username=username)
    viewer = request.user if request.user.is_authenticated else None
    tweets = user_tweets_qs(author=profile_user, viewer=viewer)
    is_following = bool(
        request.user.is_authenticated
        and request.user != profile_user
        and profile_user.followers.filter(pk=request.user.pk).exists()
    )
    return render(
        request,
        "users/profile.html",
        {
            "profile_user": profile_user,
            "tweets": tweets,
            "followers_count": profile_user.followers.count(),
            "following_count": profile_user.following.count(),
            "is_following": is_following,
        },
    )


@login_required
def edit_profile_view(request):
    if request.method == "POST":
        form = EditProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            services.update_profile(user=request.user, form=form)
            return redirect("users:profile", username=request.user.username)
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
@require_POST
def logout_view(request):
    logout(request)
    return redirect("tweets:all_tweets")


@login_required
@require_POST
def follow_user_view(request, username):
    target = get_user_by_username(username=username)
    services.follow_toggle(actor=request.user, target=target)
    return redirect("users:profile", username=username)


def followers_list_view(request, username):
    profile_user = get_user_by_username(username=username)
    return render(
        request,
        "users/followers_list.html",
        {
            "profile_user": profile_user,
            "followers": profile_user.followers.all(),
        },
    )


def following_list_view(request, username):
    profile_user = get_user_by_username(username=username)
    return render(
        request,
        "users/following_list.html",
        {
            "profile_user": profile_user,
            "following": profile_user.following.all(),
        },
    )


@login_required
def delete_account_view(request):
    if request.method == "POST":
        services.delete_account(user=request.user)
        return redirect("tweets:all_tweets")
    return render(request, "users/delete_account.html")
