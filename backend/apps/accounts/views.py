from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer
from .serializers import FirebaseLoginSerializer
from .models import User
from .services.firebase_auth import FirebaseAuthError, verify_firebase_id_token

class RegisterView(generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({'user': UserSerializer(user).data, 'access': str(refresh.access_token), 'refresh': str(refresh)}, status=status.HTTP_201_CREATED)

class LoginView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = LoginSerializer
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({'user': UserSerializer(user).data, 'access': str(refresh.access_token), 'refresh': str(refresh)})

class FirebaseLoginView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = FirebaseLoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            claims = verify_firebase_id_token(serializer.validated_data['id_token'])
        except FirebaseAuthError:
            return Response({'detail': 'RISE could not verify your Google account.'}, status=status.HTTP_401_UNAUTHORIZED)
        uid = claims.get('uid')
        email = (claims.get('email') or '').strip().lower()
        if not uid or not email:
            return Response({'detail': 'RISE could not verify your Google account.'}, status=status.HTTP_401_UNAUTHORIZED)
        user = User.objects.filter(firebase_uid=uid).first()
        if user and user.email.lower() != email:
            return Response({'detail': 'This Google account is linked to another RISE identity.'}, status=status.HTTP_409_CONFLICT)
        email_user = User.objects.filter(email__iexact=email).first()
        if user and email_user and email_user.pk != user.pk:
            return Response({'detail': 'This email is linked to another RISE identity.'}, status=status.HTTP_409_CONFLICT)
        user = user or email_user
        if user is None:
            user = User.objects.create_user(email=email, password=None, first_name=claims.get('name', '').split(' ', 1)[0], last_name=claims.get('name', '').split(' ', 1)[1] if ' ' in claims.get('name', '') else '')
        if user.firebase_uid and user.firebase_uid != uid:
            return Response({'detail': 'This RISE account is linked to another Google identity.'}, status=status.HTTP_409_CONFLICT)
        if user.firebase_uid != uid or user.avatar_url != (claims.get('picture') or ''):
            user.firebase_uid = uid
            user.avatar_url = claims.get('picture') or ''
            user.save(update_fields=('firebase_uid', 'avatar_url', 'updated_at'))
        refresh = RefreshToken.for_user(user)
        return Response({'user': UserSerializer(user).data, 'access': str(refresh.access_token), 'refresh': str(refresh)})

class CurrentUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    def get_object(self):
        return self.request.user

class LogoutView(APIView):
    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        refresh = request.data.get('refresh')
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except Exception:
                pass
        return Response(status=status.HTTP_204_NO_CONTENT)
