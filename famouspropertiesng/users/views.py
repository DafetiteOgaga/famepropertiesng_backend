from django.shortcuts import render
from django.shortcuts import render, get_list_or_404, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import User
from .serializers import ResponseUserSerializer
import json, requests, base64
from hooks.prettyprint import pretty_print_json
from django.conf import settings
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
	"countryId",
	"stateId",
	"cityId",
	"hasCities",
	"hasStates",
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
]

def get_basic_auth_header():
	token = base64.b64encode(f"{settings.IMAGEKIT_PRIVATE_KEY}:".encode()).decode()
	return {"Authorization": f"Basic {token}"}

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

		created_user_data = ResponseUserSerializer(new_user).data

		print()
		print(f"Created new user:")
		pretty_print_json(created_user_data)

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
		# print(f"Received file: {file}, type: {type(file)}")

		# print("File uploaded successfully.")
		# return Response({"result": "all goog"}, status=status.HTTP_201_CREATED)

		# if not file_id:
		# 	print("fileId is missing in the request.")
		# 	return Response({"error": "fileId is required"}, status=400)
		# if not file:
		# 	print("No file uploaded in the request.")
		# 	return Response({"error": "No file uploaded"}, status=400)

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

			# Now, upload the new file
			# upload_url = "https://upload.imagekit.io/api/v1/files/upload"
			# files = {
			# 	"file": (file.name, file.read(), file.content_type),
			# }
			# data = {
			# 	"fileName": file.name,
			# 	"useUniqueFileName": False,  # overwrite by filename
			# }

			# upload_resp = requests.post(upload_url, files=files, data=data, headers=get_basic_auth_header())

			# try:
			# 	print(f"Upload response: {upload_resp.text}")
			# 	result = upload_resp.json()
			# except ValueError:
			# 	print(f"Failed to parse JSON response: {upload_resp.text}")
			# 	return Response({"error": "Invalid JSON response", "detail": upload_resp.text}, status=upload_resp.status_code)

			# if upload_resp.status_code != 200:
			# 	print(f"File upload failed: {result}")
			# 	return Response({"error": "File upload failed", "detail": result}, status=upload_resp.status_code)
			# print("File uploaded successfully.")
			# return Response(result, status=upload_resp.status_code)

		# print("No file uploaded, proceeding with other updates.")
		# return Response({"ok": "Yippy it worked!."}, status=status.HTTP_201_CREATED)

		# data = request.POST.dict() if request.FILES else json.loads(request.body)

		# data = json.loads(request.body)
		print(f"Received data for updating user {pk}:")
		pretty_print_json(data)

		try:
			user = User.objects.get(pk=pk)
		except User.DoesNotExist:
			return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

		# Update only allowed fields
		update_fields = {}
		data_keys = data.keys()
		for field in allowed_update_fields:
			if field in data_keys:
				update_fields[field] = data[field]

		if 'password' in update_fields:
			password = update_fields.pop('password')
			user.set_password(password)

		for field, value in update_fields.items():
			setattr(user, field, value)

		user.save()
		updated_user_data = ResponseUserSerializer(user).data

		print()
		print(f"Updated user {pk}:")
		pretty_print_json(updated_user_data)

		return Response(updated_user_data, status=status.HTTP_200_OK)

# @api_view(["POST"])
# def upload_to_imagekit(request):
#     file = request.FILES.get("file")  # get file from React formData
#     if not file:
#         return Response({"error": "No file uploaded"}, status=400)

#     url = "https://upload.imagekit.io/api/v1/files/upload"
#     headers = {
#         "Authorization": "Basic " + (settings.IMAGEKIT_PRIVATE_KEY + ":").encode("ascii").decode("latin1")
#     }
#     files = {
#         "file": file,  
#         "fileName": file.name,
#     }

#     response = requests.post(url, files=files, headers=headers)
#     return Response(response.json(), status=response.status_code)