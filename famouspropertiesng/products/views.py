from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Product
from django.db import transaction
from .serializers import ProductSerializer
from hooks.deleteImage import delete_image
from hooks.prettyprint import pretty_print_json
from rest_framework.pagination import PageNumberPagination

valid_product_fields = [
	"name", "description", "fullDescription", "technicalDescription",
	"marketingDescription", "marketPrice", "discountPrice",
	"image_url_0", "fileId_0", "image_url_1", "fileId_1",
	"image_url_2", "fileId_2", "image_url_3", "fileId_3",
	"image_url_4", "fileId_4", "sold", "noOfReviewers", "store",
	"techFeature_1", "techFeature_2", "techFeature_3",
	"techFeature_4", "techFeature_5"
]
required_fields = [
	"name", "description", "fullDescription", "marketPrice",
	"discountPrice", "image_url_0", "fileId_0"
]

# Create your views here.
@api_view(['POST', 'GET'])
@csrf_exempt
def products(request, pk=None, all=None):
	if request.method == "POST":
		print("Creating new product...")
		data = json.loads(request.body)
		# print(f"Received product data: {data}")
		pretty_print_json(data)
		# return Response({"ok": "all good"}, status=201)

		# create products (list of product objects)
		products = []
		try:
			with transaction.atomic():  # entire batch is atomic
				for prod in data:
					# print("Validating product data...")
					print('Map incoming data to model fields...')
					# Map incoming data to model fields
					cleaned_data = {
						"name": prod.get("product_name", None),
						"description": prod.get("product_description", None),
						"fullDescription": prod.get("full_descriptions", None),
						"marketPrice": prod.get("market_price", None),
						"discountPrice": prod.get("discount_price", None),
						"technicalDescription": prod.get("technical_descriptions", None),
						"marketingDescription": prod.get("marketing_descriptions", None),
						"techFeature_1": prod.get("technical_feature_1", None),
						"techFeature_2": prod.get("technical_feature_2", None),
						"techFeature_3": prod.get("technical_feature_3", None),
						"techFeature_4": prod.get("technical_feature_4", None),
						"techFeature_5": prod.get("technical_feature_5", None),
						# "noOfReviewers": validated_data.get("noOfReviewers", 0),
					}

					print("Processing price fields...")
					# validating and converting price fields to float
					if cleaned_data["marketPrice"] is not None and cleaned_data["discountPrice"] is not None:
						print("Converting price fields to float...")
						try:
							print("Before conversion:", cleaned_data["marketPrice"], cleaned_data["discountPrice"])
							cleaned_data["marketPrice"] = float(cleaned_data["marketPrice"])
							cleaned_data["discountPrice"] = float(cleaned_data["discountPrice"])
							print("After conversion:", cleaned_data["marketPrice"], cleaned_data["discountPrice"])
						except (TypeError, ValueError):
							print("Invalid price format")
							return Response({"error": "Invalid: Either market and/or discount price format"}, status=400)
					else:
						print("Price fields cannot be null")
						return Response({"error": "Both market and discount price are required"}, status=400)

					print('mapping image urls and field IDs...')
					# handle mapping image_url and fileId dynamically
					for i in range(5):
						cleaned_data[f"image_url_{i}"] = prod.get(f"image_url{i}")
						cleaned_data[f"fileId_{i}"] = prod.get(f"fileId{i}")

					# get store ID
					storeID = prod.get("storeID", None)
					print(f"Store ID: {storeID}")
					if not storeID:
						print("Store ID is missing in product data")
						return Response({"error": "Store is required"}, status=400)

					print("Checking required fields...")
					# check that required fields are present
					for field in required_fields:
						if cleaned_data.get(field) is None:
							print(f"Missing required field: {field}")
							return Response({"error": f"{'Image 1' if (field.lower().startswith('image_url') or field.lower().startswith('fileid')) else field} is required"}, status=400)

					print("cleaned data...")
					pretty_print_json(cleaned_data)

					print("Creating product record in database...")
					# data contains info from React, including the uploaded image URL
					product = Product.objects.create(**cleaned_data, store_id=storeID)
					print(f"Created and appended product with ID: {product.id} to products list to be serialized")
					products.append(product)

		except ValueError as ve:
			print(f"ValueError: {ve}")
			return Response({"error": str(ve)}, status=400)

		except Exception as e:
			print(f"Error creating products: {e}")
			return Response({"error": "Failed to create products"}, status=500)

		print(f"Total products created: {len(products)}")

		# return Response({"ok": "all good"}, status=201)
		# Serialize and return created products
		serialized_products = ProductSerializer(products, many=True).data
		return Response(serialized_products, status=201)

	elif request.method == "GET":
		print(f"Received GET request for products, pk={pk}")
		print(f'fetch all param: {all}')
		# If pk is provided, fetch that specific product
		serialized_product = None
		if pk:
			product = Product.objects.get(pk=pk)
			print(f"Fetched single product")
			serialized_product = ProductSerializer(product).data
			# pretty_print_json(serialized_product)
			return Response(serialized_product, status=200)
		else:
			# Otherwise paginate the queryset
			qs = Product.objects.all().order_by('id') # from oldest to newest
			if all == 'all':
				print("Fetching all products without pagination")
				serialized_product = ProductSerializer(qs, many=True).data
				return Response(serialized_product, status=200)
			else:
				print("Fetching paginated products")
				paginator = PageNumberPagination() # DRF paginator
				paginator.page_size = 8 # default page size

				# allow client to set page size using `?page_size=...` query param
				paginator.page_size_query_param = 'page_size' # allow request for page size by users e.g ?page_size=...
				paginator.max_page_size = 100 # safety cap for page size request

				page = paginator.paginate_queryset(qs, request) # get page's items
				serializer = ProductSerializer(page, many=True).data # serialize page
				response = paginator.get_paginated_response(serializer)
				response.data["total_pages"] = paginator.page.paginator.num_pages
				return response


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
