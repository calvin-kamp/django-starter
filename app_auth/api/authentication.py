"""Authentication class that reads the JWT from a cookie."""

from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """Authenticate with the access token from the ``HttpOnly`` cookie.

    Replaces the ``Authorization`` header of the default ``JWTAuthentication``.
    Registered in ``REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]``.
    """

    def authenticate(self, request):
        raw_token = request.COOKIES.get(settings.AUTH_COOKIE["ACCESS_NAME"])

        # No cookie: the request is anonymous. Permissions decide if that's allowed.
        if raw_token is None:
            return None

        # Invalid or expired token: raises InvalidToken, which results in a 401.
        validated_token = self.get_validated_token(raw_token)

        return self.get_user(validated_token), validated_token
