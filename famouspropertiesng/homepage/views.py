from django.shortcuts import render, get_list_or_404, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
# from .models import *
# from app_bank.models import *
# from app_bank.serializers import *
# from app_location.models import Location
# from app_users.serializers import UserReadHandlersSerializer
# from .serializers import *
# from django.contrib.auth import authenticate, login, logout, get_user_model
# User = get_user_model()

# Create your views here.
@api_view(['GET'])
def home(request):
    return Response({"home": "welcome home from django server. This information is from the backend server"}, status=status.HTTP_200_OK)
