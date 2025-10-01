from django.db import models
import uuid
from django.db import models, IntegrityError, transaction

PAYMENT_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("completed", "Completed"),
    ("failed", "Failed"),
]

SHIPPING_STATUS_CHOICES = [
    ("processing", "Processing"),
    ("shipped", "Shipped"),
    ("delivered", "Delivered"),
    ("cancelled", "Cancelled"),
]

RETURN_STATUS_CHOICES = [
    ("none", "None"),
    ("requested", "Requested"),
    ("processed", "Processed"),
]

# Create your models here.
class Checkout(models.Model):
	user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='rn_checkouts', null=True, blank=True)
	checkoutID = models.UUIDField(default=uuid.uuid4, db_index=True, editable=False, unique=True)
	first_name = models.CharField(max_length=100, null=True, blank=True)
	last_name = models.CharField(max_length=100, null=True, blank=True)
	email = models.EmailField(max_length=200, null=True, blank=True, db_index=True)
	mobile_no = models.CharField(max_length=20, null=True, blank=True)
	address = models.CharField(max_length=200, null=True, blank=True)
	city = models.CharField(max_length=100, null=True, blank=True)
	state = models.CharField(max_length=100, null=True, blank=True)
	country = models.CharField(max_length=100, null=True, blank=True)
	postal_code = models.CharField(max_length=20, null=True, blank=True)
	subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # Sum of product prices
	shipping_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True)  # Sum of product prices)
	total_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # Sum of product prices
	payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='pending', db_index=True)  # e.g., pending, completed, failed
	payment_method = models.CharField(max_length=50, null=True, blank=True)  # e.g., credit card, PayPal
	shipping_status = models.CharField(max_length=50, choices=SHIPPING_STATUS_CHOICES, default='processing', db_index=True)  # e.g., processing, shipped, delivered
	shipping_method = models.CharField(max_length=100, null=True, blank=True)
	coupon_code = models.CharField(max_length=50, null=True, blank=True)
	receipt_url = models.URLField(blank=True, null=True)  # URL to payment receipt
	transaction_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
	return_or_refund_status = models.CharField(max_length=50, choices=RETURN_STATUS_CHOICES, default='none')  # e.g., none, requested, processed
	created_at = models.DateTimeField(auto_now_add=True, db_index=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Checkout {self.email} - {self.checkoutID[:8]}"

class CheckoutProduct(models.Model):
    checkout = models.ForeignKey(Checkout, on_delete=models.CASCADE, related_name="rn_checkout_products")
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2)  # price at time of purchase

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order {self.checkout.checkoutID})"