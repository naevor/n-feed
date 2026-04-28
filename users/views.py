from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegisterForm, LoginForm, EditProfileForm
from .models import CustomUser
from tweets.models import Tweet


from rest_framework.views import APIView
from rest_framework.response import Response
from .models import CustomUser
from .serializers import UserSerializer


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('users:profile', username=user.username)
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('users:profile', username=user.username)
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})

@login_required
def profile_view(request, username):
    user = get_object_or_404(CustomUser, username=username)
    user_tweets = Tweet.objects.filter(user=user).order_by('-created_at')
    
    mutual_followers = user.followers.filter(id__in=request.user.following.all())
    
    return render(
        request, 'users/profile.html', {
            'user': user,
            'tweets': user_tweets,
            'mutual_followers': mutual_followers
        }
    )

@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('users:profile', username=request.user.username)
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, 'users/edit_profile.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('tweets:all_tweets')

@login_required
def follow_user_view(request, username):
    user_to_follow = get_object_or_404(CustomUser, username=username)
    if request.user != user_to_follow:
        if user_to_follow in request.user.following.all():
            request.user.following.remove(user_to_follow)
        else:
            request.user.following.add(user_to_follow)
    return redirect('users:profile', username=username)

@login_required
def followers_list_view(request, username):
    user = get_object_or_404(CustomUser, username=username)
    followers = user.followers.all()
    return render(request, 'users/followers_list.html', {'user': user, 'followers': followers})

@login_required
def following_list_view(request, username):
    user = get_object_or_404(CustomUser, username=username)
    following = user.following.all()
    return render(request, 'users/following_list.html', {'user': user, 'following': following})

@login_required
def delete_account_view(request):
    if request.method == 'POST':
        request.user.delete()
        return redirect('tweets:all_tweets')
    return render(request, 'users/delete_account.html')


class UserListAPIView(APIView):
    def get(self, request):
        users = CustomUser.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
