from django.shortcuts import render
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .models import ProductAdvert
from hooks.deleteImage import delete_image

# Create your views here.
@api_view(['POST', 'GET'])
@csrf_exempt
def productsAdvert(request):
    if request.method == "POST":
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

        return JsonResponse({
            "id": productAdvert.id,
            "anchor": productAdvert.anchor,
            "paragraph": productAdvert.paragraph,
            "discount": productAdvert.discount,  # Convert Decimal to string for JSON serialization
            "image_url": productAdvert.image_url,
            "fileId": productAdvert.fileId,  # Include fileId in the response if needed
        }, status=201)
    elif request.method == "GET":
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

        return JsonResponse(productAdvert_list, safe=False, status=200)

@csrf_exempt
def deleteProductsAdvert(request):
    return delete_image(request, ProductAdvert)
    # return JsonResponse({"message": "Product Advert deleted successfully"}, status=200)