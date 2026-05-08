from rest_framework.routers import DefaultRouter

from .notifications import NotificationViewSet
from .tags import TagViewSet
from .tweets import TweetViewSet
from .users import UserViewSet

app_name = "api-v1"

router = DefaultRouter()
router.register("notifications", NotificationViewSet, basename="notification")
router.register("tags", TagViewSet, basename="tag")
router.register("tweets", TweetViewSet, basename="tweet")
router.register("users", UserViewSet, basename="user")

urlpatterns = router.urls
