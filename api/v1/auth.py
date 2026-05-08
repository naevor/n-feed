from rest_framework_simplejwt.views import TokenObtainPairView


class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_scope = "auth_login"
