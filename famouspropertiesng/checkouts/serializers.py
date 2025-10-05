from rest_framework import serializers
from .models import Checkout, CheckoutProduct, InstallmentPayment
from users.serializers import UserSerializerWRatings

# Create your serializers here.
class CheckoutProductSerializer(serializers.ModelSerializer):
	class Meta:
		model = CheckoutProduct
		fields = '__all__'

class InstallmentPaymentSerializer(serializers.ModelSerializer):
	class Meta:
		model = InstallmentPayment
		fields = '__all__'

class CheckoutSerializer(serializers.ModelSerializer):
	user = UserSerializerWRatings(read_only=True, allow_null=True)
	products = CheckoutProductSerializer(source='rn_checkout_products', many=True, read_only=True)
	installments = InstallmentPaymentSerializer(source='rn_installments', many=True, read_only=True)
	class Meta:
		model = Checkout
		fields = '__all__'


class ReceiptCheckoutProductSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_thumbnail = serializers.URLField(source='product.image_url_0', read_only=True)
    class Meta:
        model = CheckoutProduct
        fields = ['product_id', 'quantity', 'price', 'product_name', 'product_thumbnail']

class ReceiptInstallmentPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstallmentPayment
        fields = ['reference', 'amount_paid', 'transaction_id', 'payment_date', 'status']

class ReceiptCheckoutReceiptSerializer(serializers.ModelSerializer):
    products = ReceiptCheckoutProductSerializer(source='rn_checkout_products', many=True)
    installments = ReceiptInstallmentPaymentSerializer(source='rn_installments', many=True)
    # receipt_url = serializers.SerializerMethodField()

    class Meta:
        model = Checkout
        fields = [
            'checkoutID',
            'first_name',
            'last_name',
            'email',
            'phone_code',
            'mobile_no',
            'address',
            'city',
            'state',
            'country',
            'subtotal_amount',
            'shipping_fee',
            'total_amount',
            'remaining_balance',
            'payment_status',
            'payment_method',
            # 'receipt_url',
            'transaction_id',
            'products',
            'installments',
            'created_at',
        ]

    # def get_receipt_url(self, obj):
    #     return obj.receipt_url  # uses your unified property