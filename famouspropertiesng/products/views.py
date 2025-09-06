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
from rest_framework.pagination import PageNumberPagination

# Create your views here.
@api_view(['POST', 'GET'])
@csrf_exempt
def products(request, pk=None):
	if request.method == "POST":
		data = json.loads(request.body)
		# print(f"Received product data: {data}")

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
		print(f"Received GET request for products, pk={pk}")
		serialized_product = None
		if pk:
			product = Product.objects.get(pk=pk)
			print(f"Fetched single product")
			serialized_product = ProductSerializer(product).data
			# pretty_print_json(serialized_product)
			return Response(serialized_product, status=200)
		else:
			# total_pages = 
			# products = Product.objects.all()
			# print(f"Fetched {products.count()} products")
			# serialized_product = ProductSerializer(products, many=True).data
			# # pretty_print_json(serialized_product)
			# Otherwise paginate the queryset
			qs = Product.objects.all().order_by('id') # from oldest to newest

			paginator = PageNumberPagination() # DRF paginator
			paginator.page_size = 8 # default page size

			# allow client to set page size using `?page_size=...` query param
			paginator.page_size_query_param = 'page_size' # allow request for page size by users e.g ?page_size=...
			paginator.max_page_size = 100 # safety cap for page size request

			page = paginator.paginate_queryset(qs, request) # get page's items
			serializer = ProductSerializer(page, many=True).data # serialize page
			response = paginator.get_paginated_response(serializer)
			# serializer["total_pages"] = 4
			response.data["total_pages"] = paginator.page.paginator.num_pages
			# page_range = str(paginator.page.paginator.page_range).split('range').pop().lstrip('(').rstrip(')')
			# prange = page_range.split(',')
			# start_index = prange[0]
			# end_index = prange[1]
			# print(f"page_range: {page_range}")
			# print(f'start_index: {start_index}\nend_index: {end_index}')
			# response.data["page_range"] = page_range
			# response.data["start_index"] = start_index
			# response.data["end_index"] = end_index
			# response.data["total_pages"] = paginator.page.paginator.num_pages
			# response.data["total_pages"] = paginator.page.paginator.num_pages
			# response.data["total_pages"] = paginator.page.paginator.num_pages
			# print(f"Total pages: {response.data['total_pages']}")
			# pretty_print_json(response.data)
			# print(f"page: {paginator.page.__dir__()}")
			# print(f"paginator: {paginator.page.end_index()}")
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
