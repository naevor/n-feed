from rest_framework.routers import DefaultRouter

from .tweets import TweetViewSet
from .users import UserViewSet


app_name = 'api-v1'

router = DefaultRouter()
router.register('tweets', TweetViewSet, basename='tweet')
router.register('users', UserViewSet, basename='user')

urlpatterns = router.urls
