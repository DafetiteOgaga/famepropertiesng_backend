from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Product
from hooks.deleteImage import delete_image

# Create your views here.
@api_view(['POST', 'GET'])
@csrf_exempt
def products(request, pk=None):
	if request.method == "POST":
		data = json.loads(request.body)
		print(f"Received product data: {data}")

		# data contains info from React, including the uploaded image URL
		product = Product.objects.create(
			name=data.get("name"),
			description=data.get("description"),
			fullDescription=data.get("fullDescription"),
			marketPrice=data.get("marketPrice"),
			discountPrice=data.get("discountPrice"),
			noOfReviewers=data.get("noOfReviewers"),
			image_url=data.get("image_url"),  # <--- this comes from ImageKit
			fileId=data.get("fileId"),  # Store the ImageKit fileId if needed
		)

		return JsonResponse({
			"id": product.id,
			"name": product.name,
			"description": product.description,
			"fullDescription": product.fullDescription,
			"marketPrice": str(product.marketPrice),  # Convert Decimal to string for JSON serialization
			"discountPrice": str(product.discountPrice),  # Convert Decimal to string for JSON serialization
			"image_url": product.image_url,
			"fileId": product.fileId,  # Include fileId in the response if needed
			"sold": product.sold,  # Include sold status if needed
			"noOfReviewers": str(product.noOfReviewers),  # Convert Decimal to string for JSON serialization
		}, status=201)
	elif request.method == "GET":
		if pk:
			product = Product.objects.get(pk=pk)
			print(f"Fetched single product")
			product_data = {
				"id": product.id,
				"name": product.name,
				"description": product.description,
				"fullDescription": product.fullDescription,
				"marketPrice": str(product.marketPrice),  # Convert Decimal to string for JSON serialization
				"discountPrice": str(product.discountPrice),  # Convert Decimal to string for JSON serialization
				"image_url": product.image_url,
				"fileId": product.fileId,  # Include fileId in the response if needed
				"sold": product.sold,  # Include sold status if needed
				"noOfReviewers": str(product.noOfReviewers),  # Convert Decimal to string for JSON serialization
			}
		else:
			products = Product.objects.all()
			print(f"Fetched {products.count()} products")
			product_data = [{
				"id": product.id,
				"name": product.name,
				"description": product.description,
				"fullDescription": product.fullDescription,
				"marketPrice": str(product.marketPrice),  # Convert Decimal to string for JSON serialization
				"discountPrice": str(product.discountPrice),  # Convert Decimal to string for JSON serialization
				"image_url": product.image_url,
				"fileId": product.fileId,  # Include fileId in the response if needed
				"sold": product.sold,  # Include sold status if needed
				"noOfReviewers": str(product.noOfReviewers),  # Convert Decimal to string for JSON serialization
			} for product in products]

		return JsonResponse(product_data, safe=False, status=200)

@csrf_exempt
@api_view(['POST'])
def designateAsSold(request, pk):
	print("Marking product as sold...")
	if request.method == "POST":
		print(f"Received request to mark product {pk} as sold")
		try:
			product = Product.objects.get(pk=pk)
			product.sold = True
			product.save()
			return JsonResponse({"message": "Product marked as sold successfully"}, status=200)
		except Product.DoesNotExist:
			return JsonResponse({"error": "Product not found"}, status=404)
	else:
		return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def deleteProduct(request):
	print("Deleting product image...")
	return delete_image(request, Product)
