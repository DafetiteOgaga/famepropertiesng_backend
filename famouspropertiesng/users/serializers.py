from rest_framework import serializers
from .models import *

# Create your serializers here.
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'  # or list only fields you want

class ResponseUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'middle_name',
					'email', 'phone', 'address', 'username', 'is_staff'
					,'is_superuser'
    ]  # Exclude sensitive fields like password
