from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
import json
from .models import ProductRating
from users.models import User
from products.models import Product
from .serializers import ProductRatingSerializer
from users.serializers import UserSerializerWRatings
from hooks.prettyprint import pretty_print_json

# Create your views here.
@api_view(['POST', 'GET'])
def productRating(request, pk=None):
	print(f"Inside productRating view... with pk: {pk}")
	# return Response({"message": "Product rating received"}, status=201)
	if request.method == "POST":
		data = json.loads(request.body)
		print(f"Received product rating data:")
		pretty_print_json(data)
		

		# check that the product, user exist before creating the rating
		# check that the rating does not exsit already for this user and product
		# else update the existing rating
		userExist = User.objects.filter(pk=data.get("userId")).exists()
		productExist = Product.objects.filter(pk=data.get("productId")).exists()
		testProductExist = Product.objects.filter(pk=382).exists()
		print(f"Test product existence (pk=382): {testProductExist}")
		print(f"User exists: {userExist}\nProduct exists: {productExist}")

		# return Response({"message": "Product rating received"}, status=201)

		# data contains info from React
		product_rating = ProductRating.objects.create(
			product_id=data.get("productId"),
			user_id=data.get("userId"),
			rating=data.get("rating"),
			review=data.get("review"),
			liked=data.get("liked"),
		)

		serialized_product_rating = ProductRatingSerializer(product_rating).data
		print(f"Created new product rating:")
		pretty_print_json(serialized_product_rating)
		return Response(serialized_product_rating, status=201)

	elif request.method == "GET":
		serialized_product_rating = None
		if pk:
			try:
				user = User.objects.get(pk=pk)
				user_serialized = UserSerializerWRatings(user).data
				print(f"Fetched user with product ratings:")
				# print(user.rn_product_ratings.all())
				pretty_print_json(user_serialized)
				# product_rating = ProductRating.objects.get(pk=pk)
				# print(f"Fetched single product rating")
				# serialized_product_rating = ProductRatingSerializer(product_rating).data
				# pretty_print_json(serialized_product_rating)
			except ProductRating.DoesNotExist:
				return Response({"error": "Product rating not found."}, status=status.HTTP_404_NOT_FOUND)
		# else:
		# 	product_ratings = ProductRating.objects.all()
		# 	print(f"Fetched {product_ratings.count()} product ratings")
		# 	serialized_product_rating = ProductRatingSerializer(product_ratings, many=True).data
		# 	pretty_print_json(serialized_product_rating)

		return Response(user_serialized, status=200)