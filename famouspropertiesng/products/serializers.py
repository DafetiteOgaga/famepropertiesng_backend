from rest_framework import serializers
from .models import *
from productrating.serializers import ProductRatingSerializer

# Create your serializers here.
class ProductSerializer(serializers.ModelSerializer):
	prod_ratings = ProductRatingSerializer(many=True, read_only=True)
	total_liked = serializers.SerializerMethodField()
	total_reviewed = serializers.SerializerMethodField()
	class Meta:
		model = Product
		fields = '__all__'

	def get_total_liked(self, obj):
		return obj.prod_ratings.filter(liked=True).count()

	def get_total_reviewed(self, obj):
		return obj.prod_ratings.count()