# from django.shortcuts import render
from google.oauth2 import id_token
from google.auth.transport import requests
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.contrib.auth import get_user_model, authenticate
# (Optional) Create JWT token for your app (if using DRF SimpleJWT)
from rest_framework_simplejwt.tokens import RefreshToken
from hooks.prettyprint import pretty_print_json
import base64, hmac, hashlib, time, json
from django.http import JsonResponse
from django.conf import settings
from rest_framework_simplejwt.views import TokenObtainPairView
# from django.forms.models import model_to_dict
from users.serializers import UserSerializerWRatings
# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


# @permission_classes([AllowAny])
# @permission_classes([IsAuthenticated])
# @permission_classes([IsAdminUser]) # is_staff=True
# @permission_classes([IsAuthenticatedOrReadOnly])

User = get_user_model()

# Create your views here.
@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    token = request.data.get("token")
    try:
        # Verify token with Google
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), "216439767175-mi51mmo7b22degu0b6b1pjbdk9n8nu5c.apps.googleusercontent.com")

        # Extract user details
        email = idinfo.get("email")
        name = idinfo.get("name")
        picture = idinfo.get("picture")
        print(f"Google user info")
        pretty_print_json(idinfo)

        # Get or create local user
        user, _ = User.objects.get_or_create(email=email, defaults={"username": name})

        refresh = RefreshToken.for_user(user)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "email": email,
                "name": name,
                "picture": picture
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def imagekit_auth(request):
    print("Generating ImageKit auth token (imagekit_auth)...")
    token = str(int(time.time()))
    expire = str(int(time.time()) + 2400)  # 40 minutes (more reasonable)
    
    # Fix: The signature should be generated from token + expire only
    # NOT including the private key in the hash
    signature = hmac.new(
        settings.IMAGEKIT_PRIVATE_KEY.encode('utf-8'),
        f"{token}{expire}".encode('utf-8'),
        hashlib.sha1
    ).hexdigest()
    
    print(f"Generated ImageKit auth token: {token}, expire: {expire}, signature: {signature}")
    
    return JsonResponse({
        "token": token,
        "expire": int(expire),  # Should be integer, not string
        "signature": signature
    }, status=status.HTTP_200_OK)

@permission_classes([AllowAny])
class CookieTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")

        # 1. Check if email was provided
        if not email or not password:
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "No account found with this email."}, status=status.HTTP_404_NOT_FOUND)

        # 3. Authenticate user (checks password)
        user = authenticate(request, username=email, password=password)
        if not user:
            return Response({"error": "Incorrect password."}, status=status.HTTP_404_NOT_FOUND)

        # 4. If authentication passes, use normal JWT process
        response = super().post(request, *args, **kwargs)
        data = response.data

        # add user info to response
        data["user"] = UserSerializerWRatings(user).data
        return response
