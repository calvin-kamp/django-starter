from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import RegisterSerializer
from .utils import get_tokens_for_user, set_auth_cookies


class RegisterView(generics.CreateAPIView):
    """Create a user and log them in by setting the auth cookies."""

    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)
    authentication_classes = ()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        response = Response(
            {
                "detail": "Registration successful!",
                "user": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

        set_auth_cookies(response, get_tokens_for_user(user))

        return response
