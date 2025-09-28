from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Product, Category
from django.db import transaction
from .serializers import ProductSerializer, CategorySerializer
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
	"techFeature_4", "techFeature_5", "thumbnail_url_0",
	"numberOfItems",
]
valid_updatable_fields = [
	"name", "description", "fullDescription", "technicalDescription",
	"marketingDescription", "marketPrice", "discountPrice",
	"image_url_0", "fileId_0", "image_url_1", "fileId_1",
	"image_url_2", "fileId_2", "image_url_3", "fileId_3",
	"image_url_4", "fileId_4", "sold", "noOfReviewers",
	"techFeature_1", "techFeature_2", "techFeature_3",
	"techFeature_4", "techFeature_5", "thumbnail_url_0",
	"numberOfItems",
]
required_fields = [
	"name", "description", "fullDescription", "marketPrice",
	"discountPrice", "image_url_0", "fileId_0", "thumbnail_url_0",
	"numberOfItems",
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
						"numberOfItems": int(prod.get("number_of_items", 1)),
						"technicalDescription": prod.get("technical_descriptions", None),
						"marketingDescription": prod.get("marketing_descriptions", None),
						"techFeature_1": prod.get("technical_feature_1", None),
						"techFeature_2": prod.get("technical_feature_2", None),
						"techFeature_3": prod.get("technical_feature_3", None),
						"techFeature_4": prod.get("technical_feature_4", None),
						"techFeature_5": prod.get("technical_feature_5", None),
						"thumbnail_url_0": prod.get("thumbnail_url0", None),
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
@api_view(['PUT'])
def updateProduct(request, pk):
	print(f"Updating product with id: {pk}")
	if request.method == "PUT":
		try:
			product = Product.objects.get(pk=pk)
		except Product.DoesNotExist:
			return Response({"error": "Product not found"}, status=404)

		data = json.loads(request.body)
		print("Received update data:")
		pretty_print_json(data)

		# prodSerial = ProductSerializer(product).data
		# print("Current product data:")
		# pretty_print_json(prodSerial)
		# return Response({"ok": "all good"}, status=200)

		# # Update only valid fields
		# updated_fields = {}
		# for field in valid_updatable_fields:
		# 	if field in data:
		# 		updated_fields[field] = data[field]
		# 	else:
		# 		print(f"🚫 Field '{field}' not updatable; skipping.")

		# if not updated_fields:
		# 	return Response({"error": "No valid fields to update"}, status=400)

		print('Map incoming data to model fields...')
		cleaned_data = {
			"name": data.get("product_name", None),
			"description": data.get("product_description", None),
			"fullDescription": data.get("full_descriptions", None),
			"marketPrice": data.get("market_price", None),
			"discountPrice": data.get("discount_price", None),
			"numberOfItems": int(data.get("number_of_items", 1)),
			"technicalDescription": data.get("technical_descriptions", None),
			"marketingDescription": data.get("marketing_descriptions", None),
			"techFeature_1": data.get("technical_feature_1", None),
			"techFeature_2": data.get("technical_feature_2", None),
			"techFeature_3": data.get("technical_feature_3", None),
			"techFeature_4": data.get("technical_feature_4", None),
			"techFeature_5": data.get("technical_feature_5", None),
			"thumbnail_url_0": data.get("thumbnail_url0", None),
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
			if data.get(f"image_url{i}") is None: continue
			cleaned_data[f"image_url_{i}"] = data.get(f"image_url{i}")
			cleaned_data[f"fileId_{i}"] = data.get(f"fileId{i}")

		print("Updating fields:")
		pretty_print_json(cleaned_data)

		for field, value in cleaned_data.items():
			setattr(product, field, value)

		try:
			product.save()
			serialized_product = ProductSerializer(product).data
			print("Updated product:")
			pretty_print_json(serialized_product)
			return Response(serialized_product, status=200)
		except Exception as e:
			print(f"Error updating product: {e}")
			return Response({"error": "Failed to update product"}, status=500)
	else:
		return Response({"error": "Method not allowed"}, status=405)

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

@api_view(['GET'])
def storeProducts(request, pk):
	if request.method == 'GET':
		print(f"Received request to list products for store with id: {pk}")
		# qs = Product.objects.all().order_by('id') # from oldest to newest
		try:
			products = Product.objects.filter(store_id=pk).order_by('id')
			print(f"Fetched {products.count()} products for store {pk}")
			# serialized_products = ProductSerializer(products, many=True).data
			# else:
			print("Paginating products")
			paginator = PageNumberPagination() # DRF paginator
			paginator.page_size = 8 # default page size

			# allow client to set page size using `?page_size=...` query param
			paginator.page_size_query_param = 'page_size' # allow request for page size by users e.g ?page_size=...
			paginator.max_page_size = 100 # safety cap for page size request

			page = paginator.paginate_queryset(products, request) # get page's items
			serialized_products = ProductSerializer(page, many=True).data # serialize page
			response = paginator.get_paginated_response(serialized_products)
			response.data["total_pages"] = paginator.page.paginator.num_pages
			return response
			# return Response(serialized_products, status=200)
		except Exception as e:
			print(f"Error fetching products for store {pk}: {e}")
			return Response({"error": "Failed to fetch products"}, status=500)
	# return JsonResponse({"message": f"List products for store {pk}"})

@api_view(['GET'])
def get_categories(request):
	if request.method == 'GET':
		categories = Category.objects.all() # .only("id", "name", "description", "parent_id")

		category_map = {}
		for cat in categories:
			category_map.setdefault(cat.parent_id, []).append(cat)

		def build_tree(parent_id=None):
			children = []
			for cat in category_map.get(parent_id, []):
				children.append({
					"id": cat.id,
					"name": cat.name,
					"description": cat.description,
					"subcategories": build_tree(cat.id)
				})
			return children

		data = build_tree()  # Start from root categories
		return Response(data, status=200)
	else:
		return Response({"error": "Method not allowed"}, status=405)

@api_view(['GET'])
def query_category(request, category):
	if request.method == 'GET':
		print(f"Received request for category: {category}")
		try:
			# Get the category (case-insensitive)
			cat = Category.objects.prefetch_related(
					'rn_category_products',
				).get(
					name__iexact=category
				)
			print(f"Found category: {cat.name} (ID: {cat.id})")
			# Get all products under this category
			products = cat.rn_category_products.all().order_by('id')
			print(f"Found {products.count()} products under category '{cat.name}'")
			# print(f"products: {products}")
			print("Serializing data...")

			# Serialize category
			category_data = CategorySerializer(cat).data

			# Serialize products
			# products_data = ProductSerializer(products, many=True).data
			# print(f"Serialized {len(products_data)} products")

			print("Fetching paginated products")
			paginator = PageNumberPagination() # DRF paginator
			paginator.page_size = 8 # default page size

			# allow client to set page size using `?page_size=...` query param
			paginator.page_size_query_param = 'page_size' # allow request for page size by users e.g ?page_size=...
			paginator.max_page_size = 100 # safety cap for page size request

			print("Paginating products...")
			page = paginator.paginate_queryset(products, request) # get page's items
			print(f"Paginated to {len(page)} products for current page")
			serializer = ProductSerializer(page, many=True).data # serialize page
			print(f"Serialized {len(serializer)} products for current page")
			response = paginator.get_paginated_response(serializer)
			print("Building response data...")
			response.data["total_pages"] = paginator.page.paginator.num_pages
			response.data["category_id"] = category_data["id"]
			response.data["category"] = category_data["name"]
			response.data["category_description"] = category_data["description"]
			response.data["total_pages"] = paginator.page.paginator.num_pages
			print(f"Total pages: {response.data['total_pages']}")
			# pretty_print_json(response)

			return response

		except Category.DoesNotExist:
			print(f"Category '{category}' not found")
			return Response({"error": f"Category '{category}' not found"}, status=404)

	return Response({"error": "Method not allowed"}, status=405)