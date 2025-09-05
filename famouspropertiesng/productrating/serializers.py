from rest_framework import serializers
from .models import *

# Create your serializers here.
class ProductRatingSerializer(serializers.ModelSerializer):
	class Meta:
		model = ProductRating
		fields = '__all__'  # or list only fields you want

class SomeProductRatingSerializer(serializers.ModelSerializer):
	class Meta:
		model = ProductRating
		fields = [
			'id', 'product', 'liked'
		]  # 'user', 'created_at', 'updated_at',
			# 'review', 'rating'