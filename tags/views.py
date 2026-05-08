from django.core.paginator import Paginator
from django.shortcuts import render

from .selectors import tagged_tweets_qs

PAGE_SIZE = 20


def tag_detail(request, name):
    qs = tagged_tweets_qs(name=name, user=request.user)
    page = Paginator(qs, PAGE_SIZE).get_page(request.GET.get("page"))
    return render(
        request,
        "tags/tag_detail.html",
        {
            "tag_name": name.lower(),
            "page": page,
        },
    )
