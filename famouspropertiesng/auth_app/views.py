# from django.shortcuts import render
from google.oauth2 import id_token
from google.auth.transport import requests
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.contrib.auth import get_user_model
# (Optional) Create JWT token for your app (if using DRF SimpleJWT)
from rest_framework_simplejwt.tokens import RefreshToken
from hooks.prettyprint import pretty_print_json
import base64, hmac, hashlib, time, json
from django.http import JsonResponse
from django.conf import settings
# from django.views.decorators.csrf import csrf_exempt
# from .models import Product

User = get_user_model()

# Create your views here.
@api_view(['POST'])
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
        })
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST', 'GET'])
def generate_signature(request):
    timestamp = str(int(time.time()))
    
    signature = hmac.new(
        settings.IMAGEKIT_PRIVATE_KEY.encode(),
        timestamp.encode(),
        hashlib.sha1
    ).hexdigest()

    return JsonResponse({
        "signature": signature,
        "expire": timestamp,
        "token": settings.IMAGEKIT_PUBLIC_KEY
    })
    # return JsonResponse({"true": "true"})

@api_view(['POST', 'GET'])
def imagekit_auth(request):
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
    })
    # return JsonResponse({"true": "true"})

# @api_view(['POST', 'GET'])
# @csrf_exempt
# def products(request):
#     if request.method == "POST":
#         data = json.loads(request.body)
#         print(f"Received product data: {data}")

#         # data contains info from React, including the uploaded image URL
#         product = Product.objects.create(
#             name=data.get("name"),
#             description=data.get("description"),
#             price=data.get("price"),
#             image_url=data.get("image_url")  # <--- this comes from ImageKit
#         )

#         return JsonResponse({
#             "id": product.id,
#             "name": product.name,
#             "description": product.description,
#             "price": str(product.price),  # Convert Decimal to string for JSON serialization
#             "image_url": product.image_url,
#         }, status=201)
#     elif request.method == "GET":
#         products = Product.objects.all()
#         print(f"Fetched {products.count()} products")
#         product_list = [{
#             "id": product.id,
#             "name": product.name,
#             "description": product.description,
#             "price": str(product.price),  # Convert Decimal to string for JSON serialization
#             "image_url": product.image_url,
#         } for product in products]

#         return JsonResponse(product_list, safe=False, status=200)

