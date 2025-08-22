from django.shortcuts import render
from django.shortcuts import render, get_list_or_404, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import *
# from app_bank.models import *
# from app_bank.serializers import *
# from app_location.models import Location
# from app_users.serializers import UserReadHandlersSerializer
# from .serializers import *
# from django.contrib.auth import authenticate, login, logout, get_user_model
# User = get_user_model()

# Create your views here.
@api_view(['GET'])
def users(request, pk=None):
	users_list = User.objects.all()
	print(f'Users List: {users_list}')
	if pk:
		user = get_object_or_404(User, pk=pk)
		user_data = {
			f"user-{pk}": [
				{
					"id": user.id,
					"username": user.username,
					"email": user.email,
				}
			]
		}
	else:
		user_data = {
			"all users":
			[
				{
					"id": user.id,
					"username": user.username,
					"email": user.email,
				}
				for user in users_list
				]
		}
	return Response(user_data, status=status.HTTP_200_OK)
