from rest_framework import serializers
from .models import *
from productrating.serializers import ProductRatingSerializer, SomeProductRatingSerializer
from store.serializers import StoreSerializer

# Create your serializers here.
class UserSerializer(serializers.ModelSerializer):
    # store = StoreSerializer(source='rn_store', read_only=True) # for one-to-one relationship
    store = StoreSerializer(source='rn_store', many=True, read_only=True)
    product_ratings = SomeProductRatingSerializer(source='rn_product_ratings', many=True, read_only=True)
    class Meta:
        model = User
        fields = '__all__'  # or list only fields you want

class ResponseUserSerializer(serializers.ModelSerializer):
    store = StoreSerializer(source='rn_store', many=True, read_only=True)
    product_ratings = SomeProductRatingSerializer(source='rn_product_ratings', many=True, read_only=True)
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email',
                'mobile_no', 'address', 'username', 'is_staff',
                'city','state','country', 'image_url','fileId',
                'nearest_bus_stop','phoneCode','stateCode',
                'countryId','stateId','cityId', 'hasCities',
                'hasStates', 'product_ratings', 'is_seller',
                'store',
    ]

class UserSerializerWRatings(serializers.ModelSerializer):
    store = StoreSerializer(source='rn_store', many=True, read_only=True)
    product_ratings = SomeProductRatingSerializer(source='rn_product_ratings', many=True, read_only=True)
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email',
                'mobile_no', 'address', 'username', 'is_staff',
                'city','state','country', 'image_url','fileId',
                'nearest_bus_stop','phoneCode','stateCode',
                'countryId','stateId','cityId', 'hasCities',
                'hasStates', 'product_ratings', 'is_seller',
                'store',
    ]

# class MinuteUserSerializer(serializers.ModelSerializer):
#     store = StoreSerializer(source='rn_store', many=True, read_only=True)
#     # product_ratings = SomeProductRatingSerializer(source='rn_product_ratings', many=True, read_only=True)
#     class Meta:
#         model = User
#         fields = ['id', 'first_name', 'email',
#                 'mobile_no', 'address', 'is_staff',
#                 'city','state','country', 'nearest_bus_stop',
#                 'is_seller', 'store'
#         ]
