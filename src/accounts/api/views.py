from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

from rest_framework import generics, status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import UpdateAPIView
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from accounts.models import User
from accounts.tasks import send_verification_email
from accounts.utils import account_activation_token
from .serializers import ChangePasswordSerializer, UserSerializer, UserProfileSerializer, MyTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @extend_schema(
        responses=UserSerializer,
        examples=[
            {
                'user': {
                    'id': 1,
                    'email': 'user@example.com',
                    'name': 'User Name'
                },
                'access': 'access_token_string',
                'refresh': 'refresh_token_string'
            },
        ]
    )
    def create(self, request, *args, **kwargs):
        # Use the serializer to validate and create the new user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Send verification email via Celery
        send_verification_email.delay(user.id)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Prepare the response data
        response_data = {
            'user': UserSerializer(user, context=self.get_serializer_context()).data,
            'access': access_token,
            'refresh': refresh_token,
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


@extend_schema(
    request=MyTokenObtainPairSerializer,
    responses=MyTokenObtainPairSerializer,
)
class LoginView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=None,
        responses={
            204: OpenApiResponse(description='Logout successful'),
            400: OpenApiResponse(description='Bad Request'),
        },
    )
    def post(self, request):
        try:
            # Get the refresh token from the request data
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            # Blacklist the refresh token
            token.blacklist()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (IsAuthenticated,)

    def get_object(self, queryset=None):
        return self.request.user

    @extend_schema(
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(description='Password updated successfully.'),
            400: OpenApiResponse(description='Bad Request'),
        },
    )
    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            # Set the new password
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivateAccountView(APIView):
    @extend_schema(
        responses={
            200: OpenApiResponse(description='Account activated successfully'),
            400: OpenApiResponse(description='Invalid activation link'),
        },
    )
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)

            if account_activation_token.check_token(user, token):
                user.is_verified = True
                user.save()
                return Response({'detail': 'Account activated successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'Activation link is invalid'}, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'detail': 'Activation link is invalid'}, status=status.HTTP_400_BAD_REQUEST)



@extend_schema_view(
    get=extend_schema(
        responses=UserProfileSerializer,
    ),
    put=extend_schema(
        request=UserProfileSerializer,
        responses=UserProfileSerializer,
    ),
    patch=extend_schema(
        request=UserProfileSerializer,
        responses=UserProfileSerializer,
    ),
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user
