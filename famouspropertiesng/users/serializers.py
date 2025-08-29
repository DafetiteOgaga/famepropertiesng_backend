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
        fields = ['id', 'first_name', 'last_name', 'email',
                'mobile_no', 'address', 'username', 'is_staff'
				,'city','state','country', 'image_url','fileId',
                'nearest_bus_stop','phoneCode','stateCode'
    ]  # Exclude sensitive fields like password
