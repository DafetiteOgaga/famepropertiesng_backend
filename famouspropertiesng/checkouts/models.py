from django.db import models, IntegrityError
import uuid
from django.db.models import Sum
from django.urls import reverse
from .generate_rerference import generate_checkout_id

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
	# Unique identifier for the checkout
	checkoutID = models.CharField(
		max_length=32,
		default=generate_checkout_id,
		db_index=True,
		# editable=False,
		unique=True
	)

	# If user is registered, link to user model; else, allow null for guest checkout
	user = models.ForeignKey('users.User',
        on_delete=models.CASCADE,
        related_name='rn_checkouts',
        null=True,
        blank=True)

	# Customer details
	first_name = models.CharField(max_length=100, null=True, blank=True)
	last_name = models.CharField(max_length=100, null=True, blank=True)
	email = models.EmailField(max_length=200, null=True, blank=True, db_index=True)
	phone_code = models.CharField(max_length=10, null=True, blank=True, default="+234")
	mobile_no = models.CharField(max_length=20, null=True, blank=True)
	address = models.CharField(max_length=200, null=True, blank=True)
	lga = models.CharField(max_length=100, null=True, blank=True)
	subArea = models.CharField(max_length=100, null=True, blank=True)
	city = models.CharField(max_length=100, null=True, blank=True)
	state = models.CharField(max_length=100, null=True, blank=True)
	country = models.CharField(max_length=100, null=True, blank=True)
	# postal_code = models.CharField(max_length=20, null=True, blank=True)

	# Order details
	subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # Sum of product prices
	shipping_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True)  # Sum of product prices)
	total_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # Sum of product prices
	remaining_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # updated whenever payments are made

	# payment details
	payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='pending', db_index=True)  # e.g., pending, completed, failed
	payment_method = models.CharField(max_length=50, null=True, blank=True)  # e.g., pay now, installments, cash on delivery
	payment_channel = models.CharField(max_length=50, null=True, blank=True)  # e.g., credit card, PayPal

	# POD virtual account
	pod_account_number = models.CharField(max_length=20, null=True, blank=True)
	pod_bank_name = models.CharField(max_length=100, null=True, blank=True)
	pod_account_name = models.CharField(max_length=200, null=True, blank=True)

	# shipping details
	shipping_status = models.CharField(max_length=50, choices=SHIPPING_STATUS_CHOICES, default='processing', db_index=True)  # e.g., processing, shipped, delivered
	# shipping_method = models.CharField(max_length=100, null=True, blank=True)

	# Additional details
	# coupon_code = models.CharField(max_length=50, null=True, blank=True)

	# Payment gateway details
	# receipt_url = models.URLField(blank=True, null=True)  # URL to payment receipt
	transaction_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)

	# Return or refund status
	return_or_refund_status = models.CharField(max_length=50, choices=RETURN_STATUS_CHOICES, default='none')  # e.g., none, requested, processed

	# Timestamps
	created_at = models.DateTimeField(auto_now_add=True, db_index=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Checkout {self.email} - {self.checkoutID[:14]}"
	def total_paid(self):
		return self.rn_installments.aggregate(total=Sum("amount_paid"))["total"] or 0
	def record_installment(self, reference, amount, transaction_id, payment_channel):
		try:
			print("".rjust(50, "="))
			print(f"Recording installment payment for checkout {self.checkoutID}")
			installment, created = InstallmentPayment.objects.get_or_create(
				checkout=self,
				reference=reference,
				amount_paid=amount,
				status="completed",
				transaction_id=transaction_id,
				payment_channel=payment_channel,
				installment_number=self.rn_installments.count() + 1,
				# receipt_url=receipt_url
			)
			if not created:
				print("".rjust(50, "-"))
				print(f"Installment with reference {reference} already exists. Skipping creation.")
				# update if webhook resent
				# installment.amount_paid = amount
				# installment.transaction_id = transaction_id
				# installment.status = "completed"
				# installment.installment_number = self.rn_installments.count() + 1
				# installment.save()
		except IntegrityError:
			print("".rjust(50, "+"))
			print(f"Duplicate installment reference detected: {reference}")
			installment = InstallmentPayment.objects.get(reference=reference)
			return installment

		total_paid = self.total_paid()
		print(f"Total paid so far: {total_paid}")
		self.remaining_balance = self.total_amount - total_paid
		print(f"New remaining balance: {self.remaining_balance}")
		if self.remaining_balance < 0:
			print("Overpayment detected")
			# raise IntegrityError("Overpayment detected")
		self.payment_status = "completed" if self.remaining_balance <= 0 else "pending"
		print(f"checkout payment status updated to: {self.payment_status}")
		self.save()
		return installment
	@property
	def receipt_url(self):
		"""
		Returns the receipt URL for this checkout.
		If no installments were used, always return checkout receipt.
		If installments exist, defer to the installments to decide.
		"""
		if not self.rn_installments.exists():
			# Case 1: one-time payment
			return reverse("checkouts:receipt", kwargs={"reference": str(self.checkoutID)})
		
		# If installments exist, let the *last installment* decide
		last_payment = self.rn_installments.order_by("-id").first()
		return last_payment.receipt_url
	def save(self, *args, **kwargs):
		if not self.pk and self.total_amount:
			self.remaining_balance = self.total_amount
		super().save(*args, **kwargs)

class CheckoutProduct(models.Model):
	checkout = models.ForeignKey(Checkout, on_delete=models.CASCADE, related_name="rn_checkout_products")
	product = models.ForeignKey("products.Product", on_delete=models.CASCADE)
	quantity = models.PositiveIntegerField(default=1)
	price = models.DecimalField(max_digits=12, decimal_places=2)  # price at time of purchase

	def __str__(self):
		return f"{self.quantity} x {self.product.name} (Order {self.checkout.checkoutID})"

class InstallmentPayment(models.Model):
	checkout = models.ForeignKey(Checkout, on_delete=models.CASCADE, related_name="rn_installments")
	reference = models.CharField(max_length=100, unique=True, db_index=True)  # Paystack reference
	amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
	status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default="pending")
	payment_channel = models.CharField(max_length=50, null=True, blank=True)  # e.g., credit card, PayPal
	installment_number = models.PositiveIntegerField(default=0)  # e.g., 1 for first installment, 2 for second, etc.
	# receipt_url = models.URLField(blank=True, null=True)
	transaction_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
	payment_date = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Installment {self.amount_paid} for {self.checkout.checkoutID}"

	@property
	def receipt_url(self):
		"""
		Returns receipt URL for this installment.
		But if this is the last installment,
		the checkout receipt takes precedence.
		"""
		if self.is_last_installment():
			# Case 3: last installment → checkout receipt wins
			return reverse("checkouts:receipt", kwargs={"reference": str(self.checkout.checkoutID)})
		
		# Case 2: normal installment
		return reverse("checkouts:receipt", kwargs={"reference": str(self.reference)})

	def is_last_installment(self):
		total = self.checkout.rn_installments.count()
		return self.installment_number == total