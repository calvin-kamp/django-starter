"""Views of the authentication API.

All tokens are sent as ``HttpOnly`` cookies, never in the response body.
"""

from django.conf import settings
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenBlacklistView, TokenObtainPairView

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer
from .utils import delete_auth_cookies, get_tokens_for_user, set_auth_cookies


class RegisterView(generics.CreateAPIView):
    """Create a user and log them in.

    Endpoint: ``POST /auth/register/``
    Authentication: none, an expired access cookie must not block the request.
    """

    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)
    authentication_classes = ()

    def create(self, request, *args, **kwargs):
        """Validate the data, create the user and set both auth cookies.

        Request body:
            ``username``, ``email``, ``password``

        Responses:
            201: ``detail`` and ``user``. Access and refresh cookie are set.
            400: Field errors, e.g. email already exists or password too weak.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        response = Response(
            {
                "detail": "Registration successful!",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )

        set_auth_cookies(response, get_tokens_for_user(user))

        return response


class LoginView(TokenObtainPairView):
    """Log in with username and password.

    Endpoint: ``POST /auth/login/``
    Authentication: none, disabled by the parent class.
    """

    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        """Check the credentials and set both auth cookies.

        The tokens are removed from the response body.

        Request body:
            ``username``, ``password``

        Responses:
            200: ``detail`` and ``user``. Access and refresh cookie are set.
            401: Wrong credentials or inactive user.
        """
        response = super().post(request, *args, **kwargs)
        tokens = response.data

        set_auth_cookies(response, tokens)

        response.data = {
            "detail": "Login successful!",
            "user": tokens["user"],
        }

        return response


class LogoutView(TokenBlacklistView):
    """Log out and invalidate the refresh token.

    Endpoint: ``POST /auth/logout/``
    Authentication: none, disabled by the parent class.
    """

    def post(self, request, *args, **kwargs):
        """Blacklist the refresh token from the cookie and delete both cookies.

        Request body:
            none, the refresh token is read from the cookie.

        Responses:
            200: ``detail``. Both cookies are deleted. Also returned when there
                are no cookies or the token is already invalid.
        """
        self._blacklist_refresh_cookie(request)

        response = Response(
            {
                "detail": (
                    "Logout successful! All tokens have been deleted "
                    "and the refresh token is now invalid."
                ),
            },
            status=status.HTTP_200_OK,
        )
        delete_auth_cookies(response)

        return response

    def _blacklist_refresh_cookie(self, request):
        """Blacklist the token of the refresh cookie, if present and valid."""
        refresh_token = request.COOKIES.get(settings.AUTH_COOKIE["REFRESH_NAME"])

        if not refresh_token:
            return

        serializer = self.get_serializer(data={"refresh": refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            # Token already expired or blacklisted: the cookies are deleted anyway.
            pass
