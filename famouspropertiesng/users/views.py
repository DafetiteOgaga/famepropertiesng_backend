from django.shortcuts import render
from django.shortcuts import render, get_list_or_404, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import User
from .serializers import UserSerializerWRatings
import json, requests, base64
from django.conf import settings
from hooks.prettyprint import pretty_print_json
from hooks.cache_helpers import clear_key_and_list_in_cache, get_cache, set_cache, get_cached_response, set_cached_response
from django.core.cache import cache

cache_name = 'users'
cache_key = None
cached_data = None
# paginatore_page_size = 8

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
	"countryId",
	"stateId",
	"cityId",
	"hasCities",
	"hasStates",
	"currency",
	"currencySymbol",
	"currencyName",
	"countryEmoji",
	"lga",
	"subArea",
]

allowed_update_fields = [
	"address",
	"city",
	"country",
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
	"countryId",
	"stateId",
	"cityId",
	"hasCities",
	"hasStates",
	"currency",
	"currencySymbol",
	"currencyName",
	"countryEmoji",
	"lga",
	"subArea",
	"is_staff",
]

def get_basic_auth_header():
	token = base64.b64encode(f"{settings.IMAGEKIT_PRIVATE_KEY}:".encode()).decode()
	return {"Authorization": f"Basic {token}"}

# Create your views here.
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def users(request, pk=None):
	if request.method == 'POST':
		data = json.loads(request.body)
		print(f"Received data for new user:")
		pretty_print_json(data)

		# return Response({"ok": "all good"}, status=status.HTTP_201_CREATED)

		# user_data = {field: data.get(field) for field in allowed_fields if field in data}
		user_data = {}
		data_keys = data.keys()
		# print(f"Data keys: {data_keys}")
		print()
		for field in allowed_fields:
			if field in data_keys:
				user_data[field] = data[field]
			else:
				print(f"🚫 Field '{field}' not in received data.")

		print(f"Filtered user data to be saved:")
		pretty_print_json(user_data)

		checkEmail = data["email"]
		print(f"Checking email: {checkEmail}")

		# return Response({"error": "Email is taken."}, status=status.HTTP_400_BAD_REQUEST)

		user_exists = User.objects.filter(email=checkEmail).exists()
		# print(f"User exists query result: {user_exists}")
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

		created_user_data = UserSerializerWRatings(new_user).data

		print()
		print(f"Created new user:")
		pretty_print_json(created_user_data)

		# Invalidate cache
		clear_key_and_list_in_cache(key=cache_name)

		return Response(created_user_data, status=status.HTTP_201_CREATED)
	else:
		if pk:

			# checking for cached
			cached_data = get_cache(cache_name, pk=pk)
			if cached_data:
				return Response(cached_data, status=status.HTTP_200_OK)

			user = User.objects.filter(pk=pk)
			print(f'User: {user}')
			if not user.exists():
				return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
			user = user.first()
			user_data = UserSerializerWRatings(user).data

			# set cache
			set_cache(cache_name, user.id, user_data)

		else:

			# Check cache first
			cached_data, cache_key, tracked_keys = get_cached_response(
					cache_name, request,
					key_suffix=f"list",

					# for pagination (if pagination is set up in future)
					# key_suffix=f"{'list'}_for{('_' + all) if all == 'all' else ''}",
					# page_size=paginatore_page_size,
					# no_page_size=True if all == 'all' else False,
				)
			if cached_data:
				return Response(cached_data, status=status.HTTP_200_OK)

			users_list = User.objects.all()
			print(f'Users List: {users_list}')
			user_data = UserSerializerWRatings(users_list, many=True).data

			# Cache the new data
			set_cached_response(cache_name, cache_key, tracked_keys,
									user_data # conditionally add response.data (for pagination, if set up in future)
								)

		return Response(user_data, status=status.HTTP_200_OK)

@api_view(['POST'])
def updateUser(request, pk):
	if request.method == 'POST':
		# print(f"Update request for user ID: {pk}")
		# print(f"Request body: {request.body}")  # raw request body
		# print(f"Request.FILES: {request.FILES}")  # uploaded files
		# print(f"Request.POST: {request.POST}")  # form fields

		# file = request.FILES.get("file")
		data = json.loads(request.body)

		old_file_id = data.get("old_fileId")
		print(f"Received old_file_id: {old_file_id}")

		if old_file_id:
			# First, delete the old file using fileId
			print(f"Attempting to delete old file with ID: {old_file_id}")
			delete_url = f"https://api.imagekit.io/v1/files/{old_file_id}"
			del_resp = requests.delete(delete_url, headers=get_basic_auth_header())

			if not str(del_resp.status_code).startswith('2'):
				print(f"delete status code: {del_resp.status_code}")
				print(f"Failed to delete old file: {del_resp.text}")
				return Response({"error": "Failed to delete old file", "detail": del_resp.text}, status=del_resp.status_code)
			print(f"delete status code: {del_resp.status_code}")
			print("Old file deleted successfully.")

		# data = json.loads(request.body)
		print(f"Received data for updating user {pk}:")
		pretty_print_json(data)

		try:
			user = User.objects.get(pk=pk)
		except User.DoesNotExist:
			return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

		# if password change
		old_password = data.get("old_password", None)
		print(f"Old password provided: {old_password if old_password else 'None'}")
		if old_password:
			print(f"Password change requested for user {pk}.")
			if not user.check_password(old_password):
				print("Old password is incorrect.")
				return Response({"error": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

		# Update only allowed fields
		update_fields = {}
		data_keys = data.keys()
		for field in allowed_update_fields:
			if field in data_keys:
				previous_value = getattr(user, field, None)
				update_fields[field] = data[field]
				print(f"❎ Field '{field}' will be updated from '{previous_value}' to '{data[field]}'")
			else:
				print(f"🚫 Field '{field}' not in received data for update.")

		if 'password' in update_fields:
			password = update_fields.pop('password')
			user.set_password(password)

		for field, value in update_fields.items():
			setattr(user, field, value)

		print(f"User before saving:")
		pretty_print_json(user.__dict__)
		# return Response({"message": "all good"}, status=status.HTTP_423_LOCKED)
		user.save()
		updated_user_data = UserSerializerWRatings(user).data

		print()
		print(f"Updated user {pk}:")
		pretty_print_json(updated_user_data)

		# Invalidate cache
		clear_key_and_list_in_cache(key=cache_name, id=user.id)

		return Response(updated_user_data, status=status.HTTP_200_OK)

@api_view(['GET'])
def totalUsers(request):
	if request.method == 'GET':

		# Check cache first
		cached_data, cache_key, tracked_keys = get_cached_response(
				cache_name, request, key_suffix=f"list_all_users",
			)
		if cached_data:
			return Response(cached_data, status=status.HTTP_200_OK)

		total = User.objects.count()
		all_users_response = {"total_users": total}

		# Cache the new data
		set_cached_response(cache_name, cache_key, tracked_keys, all_users_response, timeout=(60 * 30)) # cache for 30 minutes

		return Response(all_users_response, status=status.HTTP_200_OK)
