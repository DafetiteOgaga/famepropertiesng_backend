from rest_framework import serializers
from .models import *

# Create your serializers here.
class ProductSerializer(serializers.ModelSerializer):
	class Meta:
		model = Product
		fields = '__all__'  # or list only fields you want