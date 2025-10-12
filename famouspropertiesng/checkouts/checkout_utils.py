from django.conf import settings
import requests
from hooks.cache_helpers import get_cache, set_cache
from rest_framework.response import Response
from rest_framework import status
from .models import Checkout, InstallmentPayment
from hooks.prettyprint import pretty_print_json
from decimal import Decimal
from .serializers import CheckoutSerializer, InstallmentPaymentSerializer

valid_fields = [
	# "userID", # popped from request body,
	"first_name",
	"last_name",
	"email",
	"mobile_no",
	"address",
	"city",
	"state",
	"country",
	# "postal_code",
	"subtotal_amount",
	"shipping_fee",
	"total_amount",
	# "payment_status",
	"payment_method",
	# "shipping_status",
	# "shipping_method",
	# "coupon_code",
	# "receipt_url",
	# "transaction_id",
	# "return_or_refund_status",
]

field_mapping = {
	"phoneCode": "phone_code",
	"shippingCost": "shipping_fee",
	"subTotal": "subtotal_amount",
	"totalAmount": "total_amount",
	"paymentMethod": "payment_method",
}

# variable names to pop from request body
# paymentMethod: payment_method,
# phoneCode: phone_code,
# shippingCost: shipping_fee,
# subTotal: subtotal_amount,
# totalAmount: total_amount,
# userID: user.id,


# create Paystack customer
def create_paystack_customer(user):
	"""
	Create a Paystack customer for this user (if not already created)
	"""
	if user.paystack_customer_id:
		return user.paystack_customer_id  # already exists

	url = "https://api.paystack.co/customer"
	headers = {
		"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
		"Content-Type": "application/json"
	}
	payload = {
		"email": user.email,
		"first_name": user.first_name,
		"last_name": user.last_name,
		"phone": user.mobile_no,  # optional
	}

	response = requests.post(url, headers=headers, json=payload)
	data = response.json()

	if data["status"]:
		customer_code = data["data"]["customer_code"]
		user.paystack_customer_id = customer_code
		user.save()
		return customer_code
	else:
		raise Exception(f"Failed to create Paystack customer: {data}")

# create DVA for Pay on Delivery
def assign_virtual_account(checkout):
	url = "https://api.paystack.co/dedicated_account/assign"
	headers = {
		"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
		"Content-Type": "application/json"
	}
	payload = {
		"customer": checkout.user.paystack_customer_id,  # must exist in Paystack
		"preferred_bank": "wema-bank",  # or providus-bank etc.
		"first_name": checkout.user.first_name,
		"last_name": checkout.user.last_name,
		"email": checkout.user.email,
	}
	response = requests.post(url, headers=headers, json=payload)
	data = response.json()

	if data["status"]:
		account_data = data["data"]
		checkout.pod_account_number = account_data["account_number"]
		checkout.pod_bank_name = account_data["bank"]["name"]
		checkout.pod_account_name = account_data["account_name"]
		checkout.save()
	return data

def checkout_status_fxn(reference):

	cache_name = 'checkout_status'

	# checking for cached
	cached_data = get_cache(cache_name, pk=reference)
	if cached_data:
		return Response(cached_data, status=status.HTTP_200_OK)

	try:
		# Try fetching by checkoutID first
		print(f"Fetching checkout status for reference: {reference}")
		checkout = Checkout.objects.prefetch_related('rn_checkout_products').get(checkoutID=reference)
		installment = None
		print(f'Found checkout with ID: {checkout.id} so installment is None')
	except Checkout.DoesNotExist:
		print("Checkout not found, trying installment reference...")
		# If not a checkout, maybe it's an installment reference
		try:
			print("Fetching by installment reference...")
			installment = InstallmentPayment.objects.get(reference=reference)
			checkout = installment.checkout
		except InstallmentPayment.DoesNotExist:
			print(f"Checkout/Installment with reference: {reference} not found.")
			return Response(
				{"status": "error", "message": "Checkout/Installment not found."},
				status=status.HTTP_404_NOT_FOUND
			)

	# Decide payment status
	print('found checkout: ', checkout.id)
	print("Determining payment status...")
	if checkout.payment_method == "installmental_payment":
		print("Installmental payment method detected.")
		
		if installment:
			print("Using installment status.")
			payment_status = installment.status  # status for this specific installment
		else:
			print("checking if it is the first installment.")
			installment = InstallmentPayment.objects.filter(reference=reference).first()
			# print(f"Found installment with ID: {installment.id} and installment_number: {installment.installment_number}")
			if installment and installment.installment_number == 1:
				print(f"Found installment with ID: {installment.id}")
				payment_status = installment.status  # fallback if only checkout reference is passed
			else:
				print("No installment found, defaulting to checkout payment status.")
				payment_status = checkout.payment_status
	else:
		print("Non-installmental payment method, using checkout payment status.")
		payment_status = checkout.payment_status  # pay_now

	# Build product details
	productDetails = [{
		"productId": item.product.id,
		"productName": item.product.name,
		"quantity": str(item.quantity),
		"price": str(item.price),
		"thumbnail": item.product.image_url_0
	} for item in checkout.rn_checkout_products.all()]

	# Add extra installment info if applicable
	response_data = {
		"status": payment_status,
		"productDetails": productDetails,
	}

	if checkout.payment_method == "installmental_payment":
		total_paid = checkout.total_paid()
		remaining_balance = checkout.total_amount - total_paid
		if remaining_balance < 0:
			remaining_balance = 0

		response_data["installment_info"] = {
			"total_paid": str(total_paid),
			"remaining_balance": str(remaining_balance),
			"is_fully_paid": remaining_balance == 0,
			"installments_count": checkout.rn_installments.count(),
			"last_payment_reference": installment.reference if installment else None
		}
	print("Checkout status response:")
	pretty_print_json(response_data)

	# set cache
	if payment_status == "completed":
		set_cache(cache_name, reference, response_data)

	return Response(response_data, status=status.HTTP_200_OK)

def update_product_stock(checkout):
	"""
	Update stock for all products in this checkout.
	Atomic and safe for concurrent updates.
	"""
	pass
	# build list of (product, qty)
	checkout_products = checkout.rn_checkout_products.all()
	print(''.rjust(30, 'd'))
	print(f"Checkout products: {checkout_products}")
	product_updates = [(cp.product, cp.quantity) for cp in checkout_products]
	print(''.rjust(30, 'g'))
	print(f"Products to update stock for: {product_updates}")

	# perform product quantity updates
	for product, qty in product_updates:
		print(''.rjust(30, 'h'))
		print(f"Updating stock for product {product.name} (ID: {product.id}), Qty: {qty}")
		if product.numberOfItemsAvailable < qty:
			print(f"⚠️ Not enough stock for {product.name}. Available: {product.numberOfItemsAvailable}, Requested: {qty}. Skipping stock update.")
			continue
			# raise ValueError(f"Not enough stock for {product.name}")
		product.reduce_stock(qty)

def process_successful_payment(checkout, data):
	"""
	Shared logic for handling charge.success events.
	Used by both webhook and fallback verification API.
	"""
	print("Processing successful payment (shared function)")

	# print("checkout details:")
	# pretty_print_json(CheckoutSerializer(checkout).data)
	print("checkout products:")
	# pretty_print_json(CheckoutWithProductSerializer(checkout.rn_checkout_products.all(), many=True).data)

	# return None
	amount = Decimal(data.get("amount", 0)) / 100
	reference = data.get("reference")
	transaction_id = data.get("id")
	payment_channel = data.get("channel")

	print(f"Amount: {amount}, Transaction ID: {transaction_id}, Channel: {payment_channel}")
	# Step 4: Record payment
	if checkout.payment_method == "installmental_payment":
		print("Installmental payment method detected.")
		if amount > checkout.remaining_balance:
			print(''.rjust(30, '9'))
			print("⚠️ Overpayment detected")
			# return Response(
			# 	{"status": "error", "message": "Overpayment detected"},
			# 	status=status.HTTP_400_BAD_REQUEST
			# )

		installment = checkout.record_installment(reference, amount, transaction_id, payment_channel)
		serialized_installment = InstallmentPaymentSerializer(installment).data
		serialized_checkout = CheckoutSerializer(checkout).data
		print(''.rjust(30, 'a'))
		print(f"Recorded installment id: {installment.id} for checkout id: {checkout.id}")
		# pretty_print_json(serialized_installment)
		print(''.rjust(30, 'b'))
		print('checkout:')
		# pretty_print_json(serialized_checkout)
		if installment.installment_number == 1:
			print("First installment paid, updating stock.")
			update_product_stock(checkout)
		else:
			print("Subsequent installment, stock previously updated.")

		return Response({
			"status": installment.status,
			"message": "Installment recorded",
			"total_paid": checkout.total_paid(),
			"receipt_url": checkout.receipt_url
		}, status=status.HTTP_200_OK)

	elif checkout.payment_method == "pay_now":
		print("Pay now (one-off) payment method detected.")
		# pay now (One-off payment)
		checkout.remaining_balance = 0
		checkout.payment_status = "completed"
		checkout.transaction_id = transaction_id
		checkout.payment_channel = payment_channel
		checkout.save()

		update_product_stock(checkout)

		serialized_checkout = CheckoutSerializer(checkout).data
		print(''.rjust(30, 'c'))
		print('checkout:')
		# pretty_print_json(serialized_checkout)

		return Response({
			"status": checkout.payment_status,
			"message": "Payment verified successfully",
			"receipt_url": checkout.receipt_url
		}, status=status.HTTP_200_OK)

	elif checkout.payment_method == "pay_on_delivery":
		print("Pay on Delivery payment method detected.")
		# They said Pay on Delivery, but we still got a Paystack transfer
		checkout.payment_status = "completed"
		checkout.transaction_id = transaction_id
		checkout.payment_channel = payment_channel
		checkout.save()

		update_product_stock(checkout)

		return Response({
			"status": checkout.payment_status,
			"message": "Pay on Delivery (via transfer) confirmed",
			"receipt_url": checkout.receipt_url
		}, status=status.HTTP_200_OK)

def process_failed_payment(checkout, data):
	"""
	Shared logic for handling charge.failed events.
	Used by both webhook and fallback verification API.
	"""
	print("Processing failed payment (shared function)")
	checkout.payment_status = "failed"
	print('changed payment_status to failed')
	checkout.save()

	reference = data.get("reference")

	try:
		print("Trying to update installment status to failed...")
		installment = InstallmentPayment.objects.get(reference=reference)
		installment.status = "failed"
		installment.save()
		print("Installment status updated to failed.")
	except InstallmentPayment.DoesNotExist:
		print("No associated installment found, skipping installment update.")
		pass

	return Response({
		"status": "error",
		"message": "Payment failed"
	}, status=status.HTTP_200_OK)
