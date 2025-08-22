from django.shortcuts import render
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .models import Carousel
from hooks.deleteImage import delete_image

# Create your views here.
@api_view(['POST', 'GET'])
@csrf_exempt
def carousels(request):
    if request.method == "POST":
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

        return JsonResponse({
            "id": carousel.id,
            "heading": carousel.heading,
            "paragraph": carousel.paragraph,
            "anchor": carousel.anchor,  # Convert Decimal to string for JSON serialization
            "image_url": carousel.image_url,
            "fileId": carousel.fileId,  # Include fileId in the response
        }, status=201)
    elif request.method == "GET":
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

        return JsonResponse(carousel_list, safe=False, status=200)

@csrf_exempt
def deleteCarousel(request):
    return delete_image(request, Carousel)