from django.shortcuts import render
from django.shortcuts import render, get_list_or_404, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Store
import json, requests, base64
from hooks.prettyprint import pretty_print_json
from django.conf import settings
from .serializers import StoreSerializer
from django.db import IntegrityError
from users.models import User
from users.serializers import UserSerializerWRatings

allowed_update_fields = [
	"userID",
	"store_name",
	"description",
	"store_phone_number",
	# "store_email_address",
	# "store_address",
	"image_url",
	"fileId",
	"nearest_bus_stop",
	# "business_registration_number",
	# "tax_identification_number",
	# "bank_name",
	# "bank_account_number",
	# "bank_account_name",
	# "bank_sort_code",
	# "country",
	# "countryId",
	# "hasStates",
	# "phoneCode",
	# "state",
	# "stateCode",
	# "hasCities",
	# "stateId",
	# "city",
	# "cityId",
]

# Create your views here.
@api_view(['POST', 'GET'])
def store_view(requests, pk=None):
	if requests.method == "POST":
		print(f"Inside store_view POST method... with pk: {pk}")
		data = json.loads(requests.body)
		print(f"Received store data:")
		pretty_print_json(data)

		# Update only allowed fields
		update_fields = {}
		data_keys = data.keys()
		for field in data_keys:
			if field in allowed_update_fields:
				print(f"✅ Field '{field}' allowed, adding to update_fields...")
				update_fields[field] = data[field]
			else:
				print(f"🚫 Field '{field}' not allowed, skipping...")

		print()
		print(f"allowed data:")
		pretty_print_json(update_fields)

		userID = update_fields.pop("userID", None)
		if not userID:
			return Response({"error": "userID is required"}, status=400)
		# return Response({"message": "Store creation is disabled"}, status=status.HTTP_200_OK)

		try:
			store = Store(
				user_id=userID,
				**update_fields,
			)
			user = User.objects.get(id=userID)
			user.is_seller = True
			user.save()
			store.save()
		except IntegrityError as e:
			# Handle the unique constraint failure here
			print("IntegrityError:", e)
			return Response({"error": "Store already exists for this user."}, status=400)

		serialized_store = StoreSerializer(store).data
		print(f"Created new store:")
		pretty_print_json(serialized_store)
		return Response(serialized_store, status=201)
	elif requests.method == "GET":
		serialized_store = None
		print(f"Inside store_view GET method... with pk: {pk}")
		return Response({"message": "Store retrieval is disabled"}, status=status.HTTP_200_OK)
		if pk:
			try:
				store = Store.objects.get(pk=pk)
				serialized_store = {
					"id": store.id,
					"name": store.name,
					"location": store.location,
					"ownerId": store.owner_id,
				}
				print(f"Fetched single store:")
				pretty_print_json(serialized_store)
			except Store.DoesNotExist:
				return Response({"error": "Store not found"}, status=404)
		else:
			stores = get_list_or_404(Store)
			serialized_store = [
				{
					"id": store.id,
					"name": store.name,
					"location": store.location,
					"ownerId": store.owner_id,
				} for store in stores
			]
			print(f"Fetched all stores:")
			pretty_print_json(serialized_store)

		return Response(serialized_store, status=200)

@api_view(['POST'])
def update_store(request, pk):
	if request.method == "POST":
		data = json.loads(request.body)
		print(f"Received update data for user {pk}:")
		pretty_print_json(data)

		try:
			print(f'data bf: {data}')
			id = data.pop("storeID")
			print(f'data af: {data}')
			store = Store.objects.get(id=id)
			print(f'store: {store}')
			for field, value in data.items():
				setattr(store, field, value)
			store.save()
			# print(f"Found store for user {pk}:")
			pretty_print_json(StoreSerializer(store).data)
			user = User.objects.get(id=pk)
			user_serializer = UserSerializerWRatings(user).data
			return Response(user_serializer, status=status.HTTP_200_OK)
		except Store.DoesNotExist:
			return Response({"error": "Store not found for this user"}, status=404)

		# note that pk is user not store

		# return Response({"message": "Store update is disabled"}, status=status.HTTP_200_OK)
		# Update only allowed fields
		# update_fields = {}
		# data_keys = data.keys()
		# for field in data_keys:
		# 	if field in allowed_update_fields:
		# 		print(f"✅ Field '{field}' allowed, adding to update_fields...")
		# 		update_fields[field] = data[field]
		# 	else:
		# 		print(f"🚫 Field '{field}' not allowed, skipping...")

		# print()
		# print(f"allowed update data:")
		# pretty_print_json(update_fields)

		# store = get_object_or_404(Store, pk=pk)
		# for key, value in update_fields.items():
		# 	setattr(store, key, value)
		# store.save()

		# serialized_store = StoreSerializer(store).data
		# print(f"Updated store {pk}:")
		# pretty_print_json(serialized_store)
		# return Response(serialized_store, status=200)

@api_view(['GET'])
def check_store_name(request, name):
    print(f'Checking store_name: {name}')
    exist = {
        "boolValue": True,
        "color": "green",
    }
    msg = "available"
    isStoreNameTaken = Store.objects.filter(store_name=name)
    if isStoreNameTaken:
        msg = "taken"
        exist["color"] = "#BC4B51"
    exist["message"] = f"{name} is {msg}."
    # pretty_print_json(exist)
    return Response(exist, status=status.HTTP_200_OK)

@api_view(['GET'])
def check_store_email(request, email):
    print(f'Checking store email: {email}')
    exist = {
        "boolValue": True,
        "color": "green",
    }
    msg = "available"
    # isStoreEmailTaken = Store.objects.filter(store_email=email)
    # switch back to Store model after testing
    isStoreEmailTaken = User.objects.filter(email=email)
    if isStoreEmailTaken:
        msg = "taken"
        exist["color"] = "#BC4B51"
    exist["message"] = f"{email} is {msg}."
    # pretty_print_json(exist)
    return Response(exist, status=status.HTTP_200_OK)
