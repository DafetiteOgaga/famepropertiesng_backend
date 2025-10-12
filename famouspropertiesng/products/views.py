from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
# from django.views.decorators.csrf import csrf_exempt
import json, random
from .models import Product, Category
from django.db import transaction
from .serializers import ProductSerializer, CategorySerializer
from hooks.delete_object_and_image import delete_object_and_image
from hooks.prettyprint import pretty_print_json
from rest_framework.pagination import PageNumberPagination
from django.conf import settings
from hooks.cache_helpers import clear_key_and_list_in_cache, get_cache, set_cache, get_cached_response, set_cached_response
from django.core.cache import cache
from datetime import datetime
import warnings
from django.core.paginator import UnorderedObjectListWarning
from django.db.models import Case, When

cache_name = 'product'
cache_key = None
cached_data = None
paginatore_page_size = 8

valid_product_fields = [
	"name", "description", "fullDescription", "technicalDescription",
	"marketingDescription", "marketPrice", "discountPrice",
	"image_url_0", "fileId_0", "image_url_1", "fileId_1",
	"image_url_2", "fileId_2", "image_url_3", "fileId_3",
	"image_url_4", "fileId_4", "sold", "noOfReviewers", "store",
	"techFeature_1", "techFeature_2", "techFeature_3",
	"techFeature_4", "techFeature_5", "thumbnail_url_0",
	"numberOfItemsAvailable",
]
valid_updatable_fields = [
	"name", "description", "fullDescription", "technicalDescription",
	"marketingDescription", "marketPrice", "discountPrice",
	"image_url_0", "fileId_0", "image_url_1", "fileId_1",
	"image_url_2", "fileId_2", "image_url_3", "fileId_3",
	"image_url_4", "fileId_4", "sold", "noOfReviewers",
	"techFeature_1", "techFeature_2", "techFeature_3",
	"techFeature_4", "techFeature_5", "thumbnail_url_0",
	"numberOfItemsAvailable",
]
required_fields = [
	"name", "description", "fullDescription", "marketPrice",
	"discountPrice", "image_url_0", "fileId_0", "thumbnail_url_0",
	"numberOfItemsAvailable",
]

def build_tree(category_map, parent_id=None):
	children = []
	for cat in category_map.get(parent_id, []):
		children.append({
			"id": cat.id,
			"name": cat.name,
			"description": cat.description,
			"subcategories": build_tree(category_map, cat.id)
		})
	return children

# Build a Case/When to preserve order
def preserved_order(ids):
    return Case(*[When(id=pk, then=pos) for pos, pk in enumerate(ids)])

# Create your views here.
@api_view(['POST', 'GET'])
def products(request, pk=None, all=None):
	if request.method == "POST":
		print("Creating new product...")
		data = json.loads(request.body)
		pretty_print_json(data)

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
						"numberOfItemsAvailable": int(prod.get("number_of_items_available", 1)),
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
							return Response({"error": "Invalid: Either market and/or discount price format"}, status=status.HTTP_400_BAD_REQUEST)
					else:
						print("Price fields cannot be null")
						return Response({"error": "Both market and discount price are required"}, status=status.HTTP_400_BAD_REQUEST)

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
						return Response({"error": "Store is required"}, status=status.HTTP_400_BAD_REQUEST)

					# get categories
					categories = prod.get("productCategories", None)
					print(f"Categories: {categories}")
					if not categories:
						print("Atleast one category is required.")
						return Response({"error": "Atleast one category is required."}, status=status.HTTP_400_BAD_REQUEST)

					# get the categories keys
					categories = [cat for cat in categories]
					print(f"Parsed categories: {categories}")

					cat_objs = Category.objects.filter(name__in=categories)
					print(f"Fetched {cat_objs.count()} category objects from DB")
					print(f"Category objects: {[cat.name for cat in cat_objs]}")
					print(f"checking if all categories were found...")
					print(f"db count: {cat_objs.count()}, input count: {len(categories)}, equals: {cat_objs.count() == len(categories)}")
					if cat_objs.count() != len(categories):
						print("One or more categories not found")
						return Response({"error": "One or more categories not found"}, status=status.HTTP_400_BAD_REQUEST)

					print("Checking required fields...")
					# check that required fields are present
					for field in required_fields:
						if cleaned_data.get(field) is None:
							print(f"Missing required field: {field}")
							return Response({"error": f"{'Image 1' if (field.lower().startswith('image_url') or field.lower().startswith('fileid')) else field} is required"}, status=status.HTTP_400_BAD_REQUEST)

					print("cleaned data...")

					print("Creating product record in database...")
					product = Product.objects.create(**cleaned_data, store_id=storeID)

					product.category.set(cat_objs)  # set categories
					print(f"Linked categories: {[cat.name for cat in cat_objs]} to product ID: {product.id}")

					print(f"Created and appended product with ID: {product.id} to products list to be serialized")
					products.append(product)

		except ValueError as ve:
			print(f"ValueError: {ve}")
			return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)

		except Exception as e:
			print(f"Error creating products: {e}")
			return Response({"error": "Failed to create products"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		print(f"Total products created: {len(products)}")

		# Serialize and return created products
		serialized_products = ProductSerializer(products, many=True).data
		pretty_print_json(serialized_products)

		# Invalidate cache
		clear_key_and_list_in_cache(key=cache_name)
		clear_key_and_list_in_cache(key='store_products')
		clear_key_and_list_in_cache(key='query_category')

		return Response(serialized_products, status=status.HTTP_201_CREATED)

	elif request.method == "GET":
		print(f"Received GET request for products, pk={pk}")
		print(f'fetch all param: {all}')

		# If pk is provided, fetch that specific product
		serialized_product = None
		if pk:

			# checking for cached
			cached_data = get_cache(cache_name, pk=pk)
			if cached_data:
				return Response(cached_data, status=status.HTTP_200_OK)

			try:
				product = Product.objects.get(pk=pk)
				print(f"Fetched single product from DB")
				serialized_product = ProductSerializer(product).data

				# set cache
				set_cache(cache_name, product.id, serialized_product)

				return Response(serialized_product, status=status.HTTP_200_OK)
			except Product.DoesNotExist:
				return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

		else:
			# Otherwise paginate the queryset

			# Check cache first

			# use a time-based key suffix to rotate cache every hour
			random_key = datetime.now().strftime("%Y%m%d%H")
			timeout = 60 * 60  # cache for 1 hour

			# if every 6 hours
			# now = datetime.now()
			# six_hour_block = now.hour // 6
			# random_key = f"{now.strftime('%Y%m%d')}_block{six_hour_block}"
			# timeout = 60 * 60 * 6  # cache for 6 hours

			# if every day
			# random_key = datetime.now().strftime("%Y%m%d")
   			# timeout = 60 * 60 * 24  # cache for 24 hours

			cached_data, cache_key, tracked_keys = get_cached_response(
					cache_name,
					request,
					key_suffix=f"list_for_random_product_{random_key}",
					page_size=paginatore_page_size,
					no_page_size=True if all == 'all' else False
				)
			if cached_data:
				print("Returning randomized product cached data")
				return Response(cached_data, status=status.HTTP_200_OK)

			all_ids = list(Product.objects.values_list('id', flat=True))
			print(f"all ids: {all_ids}")
			random.shuffle(all_ids)
			print(f"shuffled ids: {all_ids}")

			# select a limited number of random IDs for performance
			subset_size = paginatore_page_size * 10 if all != 'all' else len(all_ids)
			random_ids = all_ids[:subset_size]

			warnings.filterwarnings("ignore", category=UnorderedObjectListWarning)
			qs = Product.objects.filter(id__in=random_ids).order_by(preserved_order(random_ids)) # limit to 10 pages worth of random products
			# qs = Product.objects.order_by('?') # random order

			if all == 'all':
				print("Fetching all products without pagination")
				serialized_product = ProductSerializer(qs, many=True).data

				# Cache the new data
				set_cached_response(cache_name, cache_key, tracked_keys, serialized_product, timeout=timeout)

				return Response(serialized_product, status=status.HTTP_200_OK)
			else:
				print("Fetching paginated products")
				paginator = PageNumberPagination() # DRF paginator
				paginator.page_size = paginatore_page_size # default page size

				# allow client to set page size using `?page_size=...` query param
				paginator.page_size_query_param = 'page_size' # allow request for page size by users e.g ?page_size=...
				paginator.max_page_size = 100 # safety cap for page size request

				page = paginator.paginate_queryset(qs, request) # get page's items
				serializer = ProductSerializer(page, many=True).data # serialize page
				response = paginator.get_paginated_response(serializer)
				response.data["total_pages"] = paginator.page.paginator.num_pages

				# Cache the new data
				print("Caching randomized paginated product data...")
				set_cached_response(cache_name, cache_key, tracked_keys, response.data, timeout=timeout)

				return response

def deleteProduct(request):
	print("Deleting product image...")
	return delete_object_and_image(request, Product, cache_name=cache_name)

@api_view(['POST'])
def updateProduct(request, pk):
	print(f"Updating product with id: {pk}")
	if request.method == "POST":
		try:
			product = Product.objects.get(pk=pk)
		except Product.DoesNotExist:
			return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

		data = json.loads(request.body)
		print("Received update data:")
		pretty_print_json(data)

		# get categories
		categories = data.get("productCategories", None)
		print(f"Categories: {categories}")
		if not categories:
			print("Atleast one category is required.")
			return Response({"error": "Atleast one category is required."}, status=status.HTTP_400_BAD_REQUEST)

		# get the categories keys
		categories = [cat for cat in categories]
		print(f"Parsed categories: {categories}")

		cat_objs = Category.objects.filter(name__in=categories)
		print(f"Fetched {cat_objs.count()} category objects from DB")
		print(f"Category objects: {[cat.name for cat in cat_objs]}")
		print(f"checking if all categories were found...")
		print(f"db count: {cat_objs.count()}, input count: {len(categories)}, equals: {cat_objs.count() == len(categories)}")
		if cat_objs.count() != len(categories):
			print("One or more categories not found")
			return Response({"error": "One or more categories not found"}, status=status.HTTP_400_BAD_REQUEST)

		print('Map incoming data to model fields...')
		cleaned_data = {
			"name": data.get("product_name", None),
			"description": data.get("product_description", None),
			"fullDescription": data.get("full_descriptions", None),
			"marketPrice": data.get("market_price", None),
			"discountPrice": data.get("discount_price", None),
			"numberOfItemsAvailable": int(data.get("number_of_items_available", 1)),
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
				return Response({"error": "Invalid: Either market and/or discount price format"}, status=status.HTTP_400_BAD_REQUEST)
		else:
			print("Price fields cannot be null")
			return Response({"error": "Both market and discount price are required"}, status=status.HTTP_400_BAD_REQUEST)

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

			product.category.set(cat_objs)  # set categories
			print(f"Linked categories: {[cat.name for cat in cat_objs]} to product ID: {product.id}")

			serialized_product = ProductSerializer(product).data

			print("Updated product:")
			pretty_print_json(serialized_product)

			# Invalidate cache
			clear_key_and_list_in_cache(key=cache_name, id=product.id)

			return Response(serialized_product, status=status.HTTP_200_OK)
		except Exception as e:
			print(f"Error updating product: {e}")
			return Response({"error": "Failed to update product"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
	else:
		return Response({"error": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['GET'])
def likeProduct(request, pk):
	if request.method == 'GET':
		print(f"Received request to like product with id: {pk}")
		try:
			product = Product.objects.get(pk=pk)
			print(f"Updating noOfReviewers from: {product.noOfReviewers}")

			product.noOfReviewers += 1
			product.save()
			serialized_product = ProductSerializer(product).data
			print(f"Updated to {product.noOfReviewers}")
			# pretty_print_json(serialized_product)

			# Invalidate cache
			clear_key_and_list_in_cache(key=cache_name, id=product.id)

			return Response(
					{
						"id": serialized_product["id"],
						"noOfReviewers": serialized_product["noOfReviewers"]
					}, status=status.HTTP_200_OK)
		except Product.DoesNotExist:
			return Response(serialized_product, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def storeProducts(request, pk):

	cache_name = 'store_products'

	if request.method == 'GET':
		print(f"Received request to list products for store with id: {pk}")

		# Check cache first
		cached_data, cache_key, tracked_keys = get_cached_response(
			cache_name, request, key_suffix=f"list_for_store_id_{pk}",
			page_size=paginatore_page_size
		)
		if cached_data:
			return Response(cached_data, status=status.HTTP_200_OK)

		try:
			products = Product.objects.filter(store_id=pk).order_by('id')
			print(f"Fetched {products.count()} products for store {pk}")

			print("Paginating products")
			paginator = PageNumberPagination() # DRF paginator
			paginator.page_size = paginatore_page_size # default page size

			# allow client to set page size using `?page_size=...` query param
			paginator.page_size_query_param = 'page_size' # allow request for page size by users e.g ?page_size=...
			paginator.max_page_size = 100 # safety cap for page size request

			page = paginator.paginate_queryset(products, request) # get page's items
			serialized_products = ProductSerializer(page, many=True).data # serialize page
			response = paginator.get_paginated_response(serialized_products)
			response.data["total_pages"] = paginator.page.paginator.num_pages

			# Cache the new data
			set_cached_response(cache_name, cache_key, tracked_keys, response.data)

			return response
		except Exception as e:
			print(f"Error fetching products for store {pk}: {e}")
			return Response({"error": "Failed to fetch products"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_categories(request):

	cache_name = 'categories'

	if request.method == 'GET':

		# Check cache first
		cached_data, cache_key, tracked_keys = get_cached_response(
				cache_name, request, key_suffix=f"list",
				page_size=paginatore_page_size, no_page_size=True
			)
		if cached_data:
			return Response(cached_data, status=status.HTTP_200_OK)


		categories = Category.objects.all() # .only("id", "name", "description", "parent_id")

		category_map = {}
		for cat in categories:
			category_map.setdefault(cat.parent_id, []).append(cat)

		data = build_tree(category_map)  # Start from root categories

		# Cache the new data
		set_cached_response(cache_name, cache_key, tracked_keys, data, timeout=(60 * 60 * 24)) # cache for 24 hours

		return Response(data, status=status.HTTP_200_OK)
	else:
		return Response({"error": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['GET'])
def query_category(request, category):

	cache_name = 'query_category'

	if request.method == 'GET':
		print(f"Received request for category: {category}")

		# Check cache first
		# use a time-based key suffix to rotate cache every hour
		cat_random_key = datetime.now().strftime("%Y%m%d%H")
		timeout = 60 * 60  # cache for 1 hour

		# if every 6 hours
		# now = datetime.now()
		# six_hour_block = now.hour // 6
		# random_key = f"{now.strftime('%Y%m%d')}_block{six_hour_block}"
		# timeout = 60 * 60 * 6  # cache for 6 hours

		# if every day
		# random_key = datetime.now().strftime("%Y%m%d")
		# timeout = 60 * 60 * 24  # cache for 24 hours

		cached_data, cache_key, tracked_keys = get_cached_response(
			cache_name,
			request,
			key_suffix=f"list_for_{category.lower().replace(' ', '_')}_at_{cat_random_key}",
			page_size=paginatore_page_size
		)
		if cached_data:
			print("Returning randomized cached category data")
			return Response(cached_data, status=status.HTTP_200_OK)

		try:
			# Get the category (case-insensitive)
			cat = Category.objects.prefetch_related(
					'rn_category_products',
				).get(
					name__iexact=category
				)
			print(f"Found category: {cat.name} (ID: {cat.id})")

			# Get all products under this category
			# products = cat.rn_category_products.all().order_by('id')

			# Get randomized products under this category
			cat_ids = list(cat.rn_category_products.values_list('id', flat=True))
			print(f"product IDs under category '{cat.name}': {cat_ids}")
			random.shuffle(cat_ids)
			print(f"Shuffled product IDs under category '{cat.name}': {cat_ids}")

			# select a limited number of random IDs for performance
			subset_size = paginatore_page_size * 10
			cat_random_ids = cat_ids[:subset_size]

			warnings.filterwarnings("ignore", category=UnorderedObjectListWarning)
			products = cat.rn_category_products.filter(id__in=cat_random_ids).order_by(preserved_order(cat_random_ids)) # limit to 10 pages worth of random products

			print(f"Found {products.count()} products under category '{cat.name}'")
			# print(f"products: {products}")
			print("Serializing data...")

			# Serialize category
			category_data = CategorySerializer(cat).data

			print("Fetching paginated products")
			paginator = PageNumberPagination() # DRF paginator
			paginator.page_size = paginatore_page_size # default page size

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

			# Cache the new data
			print("Caching randomized category query paginated product data...")
			set_cached_response(cache_name, cache_key, tracked_keys, response.data, timeout=timeout)

			return response

		except Category.DoesNotExist:
			print(f"Category '{category}' not found")
			return Response({"error": f"Category '{category}' not found"}, status=status.HTTP_404_NOT_FOUND)

	return Response({"error": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
@permission_classes([AllowAny])
def getAvailableTotal(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		print("Received data for availability check:")
		pretty_print_json(data)

		product_ids = data.get("productIds", [])
		if not product_ids or not isinstance(product_ids, list):
			return Response({"error": "Invalid or missing 'product_ids' list"}, status=status.HTTP_400_BAD_REQUEST)

		print(f"Checking availability for product IDs: {product_ids}")

		try:
			products = Product.objects.filter(id__in=product_ids)
			availability = {str(prod.id): prod.numberOfItemsAvailable for prod in products}

			print(f"Fetched availability for {len(availability)} products from DB")

			# Ensure all requested IDs are represented in the response
			for pid in product_ids:
				availability.setdefault(str(pid), 0)  # Default to 0 if not found

			print("Availability results:")
			pretty_print_json(availability)

			return Response(availability, status=status.HTTP_200_OK)
		except Exception as e:
			print(f"Error checking availability: {e}")
			return Response({"error": "Failed to check availability"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
