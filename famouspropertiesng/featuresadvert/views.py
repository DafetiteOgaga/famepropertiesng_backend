from django.shortcuts import render
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .models import FeatureAdvert
from hooks.deleteImage import delete_image

# Create your views here..
@api_view(['POST', 'GET'])
@csrf_exempt
def featuresAdvert(request):
    if request.method == "POST":
        data = json.loads(request.body)
        print(f"Received featuresAdvert data: {data}")

        # data contains info from React, including the uploaded image URL
        featureAdvert = FeatureAdvert.objects.create(
            anchor=data.get("anchor"),
            paragraph=data.get("paragraph"),
            heading=data.get("heading"),
            # image_url=data.get("image_url")  # <--- this comes from ImageKit
        )

        return JsonResponse({
            "id": featureAdvert.id,
            "anchor": featureAdvert.anchor,
            "paragraph": featureAdvert.paragraph,
            "heading": featureAdvert.heading,  # Convert Decimal to string for JSON serialization
            # "image_url": featureAdvert.image_url,
        }, status=201)
    elif request.method == "GET":
        featuresAdvert = FeatureAdvert.objects.all()
        print(f"Fetched {featuresAdvert.count()} featureAdvert")
        featureAdvert_list = [{
            "id": featureAdvert.id,
            "anchor": featureAdvert.anchor,
            "paragraph": featureAdvert.paragraph,
            "heading": featureAdvert.heading,  # Convert Decimal to string for JSON serialization
            # "image_url": featureAdvert.image_url,
        } for featureAdvert in featuresAdvert]

        return JsonResponse(featureAdvert_list, safe=False, status=200)

@csrf_exempt
def deleteFeaturesAdverts(request):
    return delete_image(request, FeatureAdvert)
    # return JsonResponse({"message": "Feature Advert deleted successfully"}, status=200)