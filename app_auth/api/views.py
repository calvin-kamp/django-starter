"""Views of the authentication API.

All tokens are sent as ``HttpOnly`` cookies, never in the response body.
"""

from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer
from .utils import get_tokens_for_user, set_auth_cookies


class RegisterView(generics.CreateAPIView):
    """Create a user and log them in by setting the auth cookies."""

    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)
    # No authentication: an expired access cookie must not block the registration.
    authentication_classes = ()

    def create(self, request, *args, **kwargs):
        """Validate the data, create the user and set both cookies.

        Answers 201 with ``detail`` and ``user``, or 400 with the field errors.
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
    """Log in and set the ``access_token`` and ``refresh_token`` cookies.

    Permissions and authentication are disabled by the parent class.
    """

    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        """Check username and password and store both tokens in cookies.

        The tokens are removed from the response body, which only contains
        ``detail`` and ``user``. Answers 401 for wrong credentials.
        """
        response = super().post(request, *args, **kwargs)
        tokens = response.data

        set_auth_cookies(response, tokens)

        response.data = {
            "detail": "Login successful!",
            "user": tokens["user"],
        }

        return response
