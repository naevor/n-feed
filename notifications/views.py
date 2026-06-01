from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .selectors import notification_for_user, user_notifications_qs
from .services import mark_all_read as mark_all_read_service
from .services import mark_notification_read

PAGE_SIZE = 20


def _redirect_after_action(request):
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect("notifications:list")


def _wants_json(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in (
        request.headers.get("Accept") or ""
    )


def _unread_count(user):
    return user_notifications_qs(user=user).filter(is_read=False).count()


@login_required
def notification_list(request):
    qs = user_notifications_qs(user=request.user)
    page = Paginator(qs, PAGE_SIZE).get_page(request.GET.get("page"))
    return render(request, "notifications/list.html", {"page": page})


@login_required
@require_POST
def mark_read(request, pk):
    notification = notification_for_user(user=request.user, pk=pk)
    mark_notification_read(notification=notification)
    if _wants_json(request):
        return JsonResponse(
            {
                "notification_id": notification.id,
                "is_read": True,
                "unread_count": _unread_count(request.user),
            }
        )
    return _redirect_after_action(request)


@login_required
@require_POST
def mark_all_read(request):
    marked_count = mark_all_read_service(user=request.user)
    if _wants_json(request):
        return JsonResponse(
            {
                "marked_count": marked_count,
                "unread_count": _unread_count(request.user),
            }
        )
    return _redirect_after_action(request)
