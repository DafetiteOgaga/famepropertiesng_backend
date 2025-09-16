from rest_framework import serializers
from .models import *
from users.models import User

# Create your serializers here.
class StoreSerializer(serializers.ModelSerializer):
	class InlineUserSerializer(serializers.ModelSerializer):
		class Meta:
			model = User
			fields = [
				"id", "email", "mobile_no",
				"first_name", "last_name"
			]  # keep it small

	user = InlineUserSerializer(read_only=True)

	class Meta:
		model = Store
		fields = [
			'id', 'user', 'store_name',
			'nearest_bus_stop', 'description',
			'store_status', 'verified', 'rating',
			'store_phone_number',
		]

