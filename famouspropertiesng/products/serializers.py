from rest_framework import serializers
from .models import *
from productrating.serializers import SomeProductRatingSerializer
from store.serializers import StoreSerializer

# Create your serializers here.
class ProductSerializer(serializers.ModelSerializer):
	store = StoreSerializer(read_only=True)
	prod_ratings = SomeProductRatingSerializer(source='rn_prod_ratings', many=True, read_only=True)
	total_liked = serializers.SerializerMethodField()
	total_reviewed = serializers.SerializerMethodField()
	class Meta:
		model = Product
		fields = '__all__'

	def get_total_liked(self, obj):
		return obj.rn_prod_ratings.filter(liked=True).count()

	def get_total_reviewed(self, obj):
		return obj.rn_prod_ratings.count()

class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "description", "subcategories"]

    def get_subcategories(self, obj):
        # Recursively serialize children
        children = obj.rn_subcategories.all()
        return CategorySerializer(children, many=True).data