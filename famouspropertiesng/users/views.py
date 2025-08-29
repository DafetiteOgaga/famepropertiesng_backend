from django.shortcuts import render
from django.shortcuts import render, get_list_or_404, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import *
from .serializers import ResponseUserSerializer
import json
from hooks.prettyprint import pretty_print_json
# from app_bank.models import *
# from app_bank.serializers import *
# from app_location.models import Location
# from app_users.serializers import UserReadHandlersSerializer
# from .serializers import *
# from django.contrib.auth import authenticate, login, logout, get_user_model
# User = get_user_model()

allowed_fields = [
	"address",
	"city",
	"country",
	"email",
	"first_name",
	"last_name",
	"mobile_no",
	"nearest_bus_stop",
	"password",
	"phoneCode",
	"state",
	"stateCode",
	"username",
	"image_url",
	"fileId",
]

# Create your views here.
@api_view(['GET', 'POST'])
def users(request, pk=None):
	if request.method == 'POST':
		data = json.loads(request.body)
		print(f"Received data for new user:")
		pretty_print_json(data)

		# user_data = {field: data.get(field) for field in allowed_fields if field in data}
		user_data = {}
		data_keys = data.keys()
		print(f"Data keys: {data_keys}")
		for field in allowed_fields:
			if field in data_keys:
				user_data[field] = data[field]
			else:
				print(f"Field '{field}' not in received data.")

		print(f"Filtered user data to be saved:")
		pretty_print_json(user_data)

		checkEmail = data["email"]
		print(f"Checking email: {checkEmail}")

		# return Response({"error": "Email is taken."}, status=status.HTTP_400_BAD_REQUEST)

		user_exists = User.objects.filter(email=checkEmail).exists()
		print(f"User exists query result: {user_exists}")
		if user_exists:
			print("User with this email exists.")
			return Response({"error": "Email is Taken."}, status=status.HTTP_400_BAD_REQUEST)
		print("Email is unique, proceeding to create user.")

		password = user_data.pop("password", None)  # remove password from dict if present
		new_user = User.objects.create(**user_data)

		if password:
			new_user.set_password(password)
			# print(f"Hashed password (before saving): {new_user.password}")
			new_user.save()

		created_user_data = ResponseUserSerializer(new_user).data

		return Response(created_user_data, status=status.HTTP_201_CREATED)
	else:
		if pk:
			user = User.objects.filter(pk=pk)
			print(f'User: {user}')
			if not user.exists():
				return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
			user_data = ResponseUserSerializer(user.first()).data
		else:
			users_list = User.objects.all()
			print(f'Users List: {users_list}')
			user_data = ResponseUserSerializer(users_list, many=True).data
		return Response(user_data, status=status.HTTP_200_OK)

# @api_view(['GET'])
# def allUsers(request):
# 	users = User.objects.all()
# 	users_serializer = ResponseUserSerializer(users, many=True).data
# 	# print(f'All Users: {users_serializer}')
# 	return Response({"allUsers": users_serializer}, status=status.HTTP_200_OK)
