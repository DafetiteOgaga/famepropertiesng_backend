from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Product
from .serializers import ProductSerializer
from hooks.deleteImage import delete_image
from hooks.prettyprint import pretty_print_json

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

		serialized_product = ProductSerializer(product).data
		return Response(serialized_product, status=201)

	elif request.method == "GET":
		serialized_product = None
		if pk:
			product = Product.objects.get(pk=pk)
			print(f"Fetched single product")
			serialized_product = ProductSerializer(product).data
			pretty_print_json(serialized_product)
		else:
			products = Product.objects.all()
			print(f"Fetched {products.count()} products")
			serialized_product = ProductSerializer(products, many=True).data
			pretty_print_json(serialized_product)

		return Response(serialized_product, status=200)

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

@api_view(['GET'])
def likeProduct(request, pk):
	if request.method == 'GET':
		print(f"Received request to like product with id: {pk}")
		try:
			product = Product.objects.get(pk=pk)
			print(f"Updating noOfReviewers from: {product.noOfReviewers}")
			# serialized_product = ProductSerializer(product).data
			# pretty_print_json(serialized_product)
			# print('\n')
			product.noOfReviewers += 1
			product.save()
			serialized_product = ProductSerializer(product).data
			print(f"Updated to {product.noOfReviewers}")
			# pretty_print_json(serialized_product)
			return Response(
					{
						"id": serialized_product["id"],
						"noOfReviewers": serialized_product["noOfReviewers"]
					}, status=200)
			# return Response({"noOfReviewers": "product"}, status=200)
		except Product.DoesNotExist:
			return Response(serialized_product, status=404)
	# else:
	# 	return Response({"error": "Method not allowed"}, status=405)
