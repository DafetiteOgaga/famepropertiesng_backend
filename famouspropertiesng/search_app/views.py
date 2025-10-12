from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from users.models import User
from store.models import Store
from hooks.cache_helpers import get_cache, set_cache
from django.core.cache import cache

cache_name = None
cache_key = None
cached_data = None
# paginatore_page_size = 8

# Create your views here.
@api_view(['GET'])
def check_email(request, email):

	cache_name = 'check_email'

	# checking for cached
	cached_data = get_cache(cache_name, pk=email)
	if cached_data:
		return Response(cached_data, status=status.HTTP_200_OK)

	print(f'Checking email: {email}')
	exist = {
		"boolValue": True,
		"color": "green",
	}
	msg = "available"
	user = User.objects.filter(email=email)
	if user:
		msg = "taken"
		exist["color"] = "#BC4B51"
	exist["message"] = f"{email} is {msg}."
	# pretty_print_json(exist)

	# set cache
	if user:
		set_cache(cache_name, email, exist)

	return Response(exist, status=status.HTTP_200_OK)

@api_view(['GET'])
def check_store_name(request, name):

	cache_name = 'check_store_name'

	# checking for cached
	cached_data = get_cache(cache_name, pk=name)
	if cached_data:
		return Response(cached_data, status=status.HTTP_200_OK)

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

	# set cache
	if isStoreNameTaken:
		set_cache(cache_name, name, exist)

	return Response(exist, status=status.HTTP_200_OK)

@api_view(['GET'])
def check_store_email(request, email):

	cache_name = 'check_store_email'

	# checking for cached
	cached_data = get_cache(cache_name, pk=email)
	if cached_data:
		return Response(cached_data, status=status.HTTP_200_OK)

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

	# set cache
	if isStoreEmailTaken:
		set_cache(cache_name, email, exist)

	return Response(exist, status=status.HTTP_200_OK)
