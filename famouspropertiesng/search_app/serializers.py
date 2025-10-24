from rest_framework import serializers
from .models import *
from users.models import User
from store.serializers import StoreSerializer
from productrating.serializers import SomeProductRatingSerializer
from checkouts.models import InstallmentPayment, Checkout, CheckoutProduct
from checkouts.serializers import CheckoutProductSerializer
from store.models import Store
from products.serializers import ProductWOCatSerializer, ProductWTotalNumAndStoreSerializer
from products.models import Product

class InlineUserSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = [
			"id", "email", "mobile_no",
			"first_name", "last_name"
		]  # keep it small

class SearchedStoreSerializer(serializers.ModelSerializer):
	user = InlineUserSerializer(read_only=True)
	class Meta:
		model = Store
		fields = [
			'id', 'user', 'store_name',
			'nearest_bus_stop', 'store_email_address',
			'store_status', 'verified', 'rating',
			'store_phone_number', 'store_address',
			'created_at', 'updated_at',
		]


class SeachedInstallmentPaymentSerializer(serializers.ModelSerializer):
	class Meta:
		model = InstallmentPayment
		fields = '__all__'

# Create your serializers here.
class SearchedUserSerializer(serializers.ModelSerializer):
	store = SearchedStoreSerializer(source='rn_store', many=True, read_only=True)
	unfulfilled_installments = serializers.SerializerMethodField()
	unsettled_delivery_payments = serializers.SerializerMethodField()
	# unfulfilled_checkout_ids = serializers.SerializerMethodField()
	class Meta:
		model = User
		fields = ['id', 'first_name', 'last_name', 'email',
				'mobile_no', 'address', 'username', 'is_staff',
				'city','state','country',
				'nearest_bus_stop','phoneCode',
				'is_seller',
				'currency', 'currencySymbol', 'currencyName',
				'countryEmoji', 'store',
				'unfulfilled_installments',
				'unsettled_delivery_payments',
				'lga', 'subArea', 'last_login', 'is_active',
				'date_joined',
	]
	def get_unfulfilled_installments(self, obj):
		# print(''.rjust(60,'i'))
		# print(f"USER OBJ: {obj}")
		# insallment = obj.rn_checkouts.filter(
		# 		payment_method="installmental_payment",
		# 		payment_status='pending'
		# 	)
		# 	# status = "pending"
		
		# print(f"INSTALLMENT ITEMS:")
		# for idx, item in enumerate(insallment):
		# 	print(f"{idx+1}: {item}")

		return obj.rn_checkouts.filter(
			payment_method="installmental_payment",
			payment_status='pending',
			# rn_installments__status__in=["pending", "partial"]
		).values_list("checkoutID", flat=True)

	def get_unsettled_delivery_payments(self, obj):
		# print(''.rjust(60,'d'))
		# print(f"USER OBJ: {obj}")
		# pod = obj.rn_checkouts.filter(
		# 		payment_method="pay_on_delivery",
		# 		payment_status='pending'
		# 	)
		# 	# status = "pending"
		
		# print(f"POD ITEMS:")
		# for idx, item in enumerate(pod):
		# 	print(f"{idx+1}: {item}")

		return obj.rn_checkouts.filter(
			payment_method="pay_on_delivery",
			payment_status='pending',
			# shipping_status__in=["shipped", "delivered"]
		).values_list("checkoutID", flat=True)

class SearchedCheckoutProductMiniSerializer(serializers.ModelSerializer):
	product = ProductWTotalNumAndStoreSerializer(read_only=True)
	class Meta:
		model = CheckoutProduct
		fields = '__all__'

class SearchedCheckoutSerializer(serializers.ModelSerializer):
	products = SearchedCheckoutProductMiniSerializer(source='rn_checkout_products', many=True, read_only=True)
	installments = SeachedInstallmentPaymentSerializer(source='rn_installments', many=True, read_only=True)
	shipped_by = InlineUserSerializer(read_only=True)
	delivered_by = InlineUserSerializer(read_only=True)
	cancelled_by = InlineUserSerializer(read_only=True)
	class Meta:
		model = Checkout
		# fields = '__all__'
		exclude = ['id', 'user', 'pod_account_number', 'pod_bank_name',
					'pod_account_name']

class SearchedCheckoutProductSerializer(serializers.ModelSerializer):
	store = SearchedStoreSerializer(read_only=True)
	# prod_ratings = SomeProductRatingSerializer(source='rn_prod_ratings', many=True, read_only=True)
	# total_liked = serializers.SerializerMethodField()
	# total_reviewed = serializers.SerializerMethodField()
	class Meta:
		model = Product
		# fields = '__all__'
		exclude = ['category', 'thumbnail_url_0', 'image_url_0',
					'image_url_1', 'image_url_2', 'image_url_3',
					'image_url_4', 'fileId_0', 'fileId_1',
					'fileId_2', 'fileId_3', 'fileId_4', 'sold']
