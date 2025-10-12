from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly
# from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
import json
from .models import Carousel
from hooks.delete_object_and_image import delete_object_and_image
from hooks.custom_auth import is_staff
from hooks.cache_helpers import clear_key_and_list_in_cache, get_cached_response, set_cached_response
from django.core.cache import cache

cache_name = 'carousels'
cache_key = None
cached_data = None
# paginatore_page_size = 8

# Create your views here.
# @permission_classes([IsAuthenticatedOrReadOnly])
@api_view(['POST', 'GET'])
def carousels(request):
	if request.method == "POST":

		response = is_staff(request)
		if response: return response

		data = json.loads(request.body)
		print(f"Received carousel data: {data}")

		# data contains info from React, including the uploaded image URL
		carousel = Carousel.objects.create(
			heading=data.get("heading"),
			paragraph=data.get("paragraph"),
			anchor=data.get("anchor"),
			image_url=data.get("image_url"),  # <--- this comes from ImageKit
			fileId=data.get("fileId"),  # Store the ImageKit fileId
		)

		# Invalidate cache
		clear_key_and_list_in_cache(key=cache_name)

		return Response({
			"id": carousel.id,
			"heading": carousel.heading,
			"paragraph": carousel.paragraph,
			"anchor": carousel.anchor,  # Convert Decimal to string for JSON serialization
			"image_url": carousel.image_url,
			"fileId": carousel.fileId,  # Include fileId in the response
		}, status=status.HTTP_201_CREATED)
	elif request.method == "GET":

		# Check cache first
		cached_data, cache_key, tracked_keys = get_cached_response(
				cache_name, request, key_suffix=f"list",
				no_page_size=True,
			)
		if cached_data:
			return Response(cached_data, status=status.HTTP_200_OK)

		print("Fetching all carousels")
		carousels = Carousel.objects.all()
		print(f"Fetched {carousels.count()} carousels")
		carousel_list = [{
			"id": carousel.id,
			"heading": carousel.heading,
			"paragraph": carousel.paragraph,
			"anchor": carousel.anchor,  # Convert Decimal to string for JSON serialization
			"image_url": carousel.image_url,
			"fileId": carousel.fileId,  # Include fileId in the response
		} for carousel in carousels]

		# Cache the new data
		set_cached_response(
			cache_name,
			cache_key,
			tracked_keys,
			carousel_list,
		)

		return Response(carousel_list, status=status.HTTP_200_OK)

@api_view(['POST'])
def deleteCarousel(request):
	response = is_staff(request)
	if response: return response
	return delete_object_and_image(request, Carousel, cache_name=cache_name)
