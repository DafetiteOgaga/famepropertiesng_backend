from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from django.test import RequestFactory
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
import json
from .models import FeatureAdvert, FeatureAdvertImage
from hooks.prettyprint import pretty_print_json
from hooks.delete_object_and_image import delete_object_and_image
from hooks.custom_auth import is_staff
from hooks.cache_helpers import clear_key_and_list_in_cache, get_cached_response, set_cached_response
from django.core.cache import cache

cache_name = 'featuresAdvert'
cache_key = None
cached_data = None
# paginatore_page_size = 8

# Create your views here..
@api_view(['POST', 'GET'])
def featuresAdvert(request):
	if request.method == "POST":

		response = is_staff(request)
		if response: return response

		data = json.loads(request.body)
		print(f"Received featuresAdvert data:")
		pretty_print_json(data)

		# check if updating image
		file_id = data.get("fileId")
		print(f"file_id: {file_id}")
		text_fields = data.get("text_fields", False)
		print(f"text_fields: {text_fields}")
		if file_id:
			print("Updating existing FeatureAdvert image...")
			old_image = FeatureAdvertImage.objects.first()
			print(f"Old image: {old_image.fileId if old_image else 'None'}")
			delete_success = True if not old_image else False
			if old_image:
				factory = RequestFactory()
				django_request = factory.post(
									"/",
									data={
										"custom_request": True,
										"fileId": old_image.fileId},
										content_type="application/json",
									)
				drf_request = Request(django_request)

				# delete old object and image
				delete_success = delete_object_and_image(
					drf_request,
					FeatureAdvertImage,
					cache_name=cache_name
				)
			if delete_success:
				print("Old image deleted successfully.")
				print(f"Creating new FeatureAdvertImage with fileId: {file_id}")
				featureAdvert_image = FeatureAdvertImage.objects.create(
					image_url=data.get("image_url"),  # <--- this comes from ImageKit
					fileId=data.get("fileId"),  # Store the ImageKit fileId
				)
				print(f"New image created: {featureAdvert_image.fileId}")
		if text_fields:
			print("Creating new FeatureAdvert text fields...")
			# data contains info from React, including the uploaded image URL
			featureAdvert = FeatureAdvert.objects.create(
				anchor=data.get("anchor"),
				paragraph=data.get("paragraph"),
				heading=data.get("heading"),
			)
			print(f"New FeatureAdvert texts created with ID: {featureAdvert.id}")

		# Invalidate cache
		clear_key_and_list_in_cache(key=cache_name)

		return Response({
			# for texts fields
			"id": featureAdvert.id if text_fields else None,
			"anchor": featureAdvert.anchor if text_fields else None,
			"paragraph": featureAdvert.paragraph if text_fields else None,
			"heading": featureAdvert.heading if text_fields else None,
			# for image fields
			"image_id": featureAdvert_image.id if file_id else None,
			"image_url": featureAdvert_image.image_url if file_id else None,
			"fileId": featureAdvert_image.fileId if file_id else None,
		}, status=status.HTTP_201_CREATED)
	elif request.method == "GET":

		# Check cache first
		cached_data, cache_key, tracked_keys = get_cached_response(
				cache_name, request, key_suffix=f"list",
				no_page_size=True,
			)
		if cached_data:
			return Response(cached_data, status=status.HTTP_200_OK)

		featuresAdvert = FeatureAdvert.objects.all()
		featureAdvert_image = FeatureAdvertImage.objects.first()
		print(f"Fetched {featuresAdvert.count()} featureAdvert")
		featuresAdvert_list = [{
			"id": featureAdvert.id,
			"anchor": featureAdvert.anchor,
			"paragraph": featureAdvert.paragraph,
			"heading": featureAdvert.heading,  # Convert Decimal to string for JSON serialization
		} for featureAdvert in featuresAdvert]

		feature_response_list = {
			"featuresAdvert": featuresAdvert_list,
			"featureAdvert_image": {
				"image_id": featureAdvert_image.id if featureAdvert_image else None,
				"image_url": featureAdvert_image.image_url if featureAdvert_image else None,
				"fileId": featureAdvert_image.fileId if featureAdvert_image else None,
			}
		}

		# Cache the new data
		set_cached_response(
			cache_name,
			cache_key,
			tracked_keys,
			feature_response_list,
		)

		return Response(feature_response_list, status=status.HTTP_200_OK)

@api_view(['POST'])
def deleteFeaturesAdverts(request):
	response = is_staff(request)
	if response: return response
	return delete_object_and_image(request, FeatureAdvert, cache_name=cache_name)
