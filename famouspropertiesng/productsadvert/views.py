from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly
# from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework import status
import json
from .models import ProductAdvert
from hooks.delete_object_and_image import delete_object_and_image
from hooks.custom_auth import is_staff
from hooks.cache_helpers import clear_key_and_list_in_cache, get_cached_response, set_cached_response
from django.core.cache import cache

cache_name = 'productsAdvert'
cache_key = None
cached_data = None
# paginatore_page_size = 8

# Create your views here.
# @permission_classes([IsAuthenticatedOrReadOnly])
@api_view(['POST', 'GET'])
def productsAdvert(request):
	if request.method == "POST":

		response = is_staff(request)
		if response: return response

		data = json.loads(request.body)
		print(f"Received productsAdvert data: {data}")

		# data contains info from React, including the uploaded image URL
		productAdvert = ProductAdvert.objects.create(
			anchor=data.get("anchor"),
			paragraph=data.get("paragraph"),
			discount=data.get("discount"),
			image_url=data.get("image_url"),  # <--- this comes from ImageKit
			fileId=data.get("fileId"),  # Store the ImageKit fileId if needed
		)

		# Invalidate cache
		clear_key_and_list_in_cache(key=cache_name)

		return Response({
			"id": productAdvert.id,
			"anchor": productAdvert.anchor,
			"paragraph": productAdvert.paragraph,
			"discount": productAdvert.discount,  # Convert Decimal to string for JSON serialization
			"image_url": productAdvert.image_url,
			"fileId": productAdvert.fileId,  # Include fileId in the response if needed
		}, status=status.HTTP_201_CREATED)
	elif request.method == "GET":

		# Check cache first
		cached_data, cache_key, tracked_keys = get_cached_response(
				cache_name, request, key_suffix=f"list",
				no_page_size=True,
			)
		if cached_data:
			return Response(cached_data, status=status.HTTP_200_OK)

		productsAdvert = ProductAdvert.objects.all()
		print(f"Fetched {productsAdvert.count()} productAdvert")
		productAdvert_list = [{
			"id": productAdvert.id,
			"anchor": productAdvert.anchor,
			"paragraph": productAdvert.paragraph,
			"discount": productAdvert.discount,  # Convert Decimal to string for JSON serialization
			"image_url": productAdvert.image_url,
			"fileId": productAdvert.fileId,  # Include fileId in the response if needed
		} for productAdvert in productsAdvert]

		# Cache the new data
		set_cached_response(
			cache_name,
			cache_key,
			tracked_keys,
			productAdvert_list,
		)

		return Response(productAdvert_list, status=status.HTTP_200_OK)

@api_view(['POST'])
def deleteProductsAdvert(request):
	response = is_staff(request)
	if response: return response
	return delete_object_and_image(request, ProductAdvert, cache_name=cache_name)
