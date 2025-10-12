from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Checkout, CheckoutProduct, InstallmentPayment
from products.models import Product
import json, requests, uuid, hmac, hashlib
from django.conf import settings
from .serializers import CheckoutSerializer, ReceiptCheckoutReceiptSerializer
from users.models import User
from hooks.cache_helpers import get_cache, set_cache
from .checkout_utils import create_paystack_customer, assign_virtual_account
from .checkout_utils import process_successful_payment, process_failed_payment
from .checkout_utils import checkout_status_fxn, valid_fields, field_mapping

cache_name = 'checkouts'
cache_key = None
cached_data = None
# paginatore_page_size = 8

# Create your views here.
@api_view(['GET'])
def generate_reference(request):
    while True:
        reference = uuid.uuid4()
        is_checkout = Checkout.objects.filter(checkoutID=reference).exists()
        is_installment = InstallmentPayment.objects.filter(reference=reference).exists()
        if not is_checkout and not is_installment:
            reference = str(reference).replace("-", "")
            print(f"Generated unique reference: {reference}")
            return Response({"reference": reference}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def checkouts(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		print("Received checkout data:")
		print(f'data: {data}')
		cleaned_data = {key: value for key, value in data.items() if key in valid_fields}
		for frontend_key, backend_key in field_mapping.items():
			cleaned_data[backend_key] = data.get(frontend_key)
		userID = data.get('userID', None)
		pod = data.get('paymentMethod', None) == "pay_on_delivery"
		instllPay = data.get('paymentMethod', None) == "installmental_payment"
		print(f"userID: {userID}, pod: {pod}. installmental_payment: {instllPay}")
		print("Cleaned data:")
		print(f'cleaned_data: {cleaned_data}')

		# check if user has an account
		if not userID and (pod or instllPay):
			paymentText = "Pay on Delivery" if pod else "Installmental Payment" if instllPay else "Pay Now"
			notLoggedIn = f"You must be logged in to use {paymentText} option."
			print(notLoggedIn)
			return Response({
				"status": "error",
				"message": notLoggedIn
			}, status=status.HTTP_400_BAD_REQUEST)
		checkout_instance = Checkout.objects.create(user_id=userID, **cleaned_data)

		if checkout_instance.payment_method == "pay_on_delivery":
			try:
				user = checkout_instance.user
				if user and not user.paystack_customer_id:
					create_paystack_customer(user)
				assign_virtual_account(checkout_instance)
				return Response({
					"status": "success",
					"message": "Dedicated virtual account created for POD",
					"bank_name": checkout_instance.pod_bank_name,
					"account_number": checkout_instance.pod_account_number,
					"account_name": checkout_instance.pod_account_name,
				}, status=status.HTTP_200_OK)
			except Exception as e:
				print(f"Error assigning virtual account: {e}")
				return Response({
					"status": "error",
					"message": "Failed to assign virtual account for POD"
				}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		cart_details = data.get("cartDetails", [])
		for product in cart_details:
			product_id = product.get("productId")
			quantity = product.get("productQuantity", 1)
			current_product_price = product.get("productPrice", 0.00)
			if product_id:
				try:
					product_instance = Product.objects.get(pk=product_id)
					CheckoutProduct.objects.create(
						checkout=checkout_instance,
						product=product_instance,
						quantity=quantity,
						price=current_product_price,
					)
				except Product.DoesNotExist:
					print(f"Product with ID {product_id} does not exist.")
			else:
				print("Product ID is missing in cart details.")
		print(f"Created checkout with ID: {checkout_instance.id}")
		reference = checkout_instance.checkoutID.hex
		print(f"Generating unique reference...: {reference}")
		serialized_checkout = CheckoutSerializer(checkout_instance).data
		print(f'serialized_checkout: {serialized_checkout}')
		response = {
			'reference': reference,
			'checkout_id': checkout_instance.id,
			'amount': int(checkout_instance.total_amount),  # convert to kobo
			'email': checkout_instance.email,
			'payment_method': checkout_instance.payment_method,
		}
		print(f"Generated reference: {response['reference']}")
		return Response(response, status=status.HTTP_200_OK)
	return Response({"message": "Checkouts endpoint is under construction."}, status=status.HTTP_200_OK)

@api_view(['GET'])
def checkout_receipt_view(request, reference):
	"""
	Fetch checkout receipt data by checkoutID or installment reference.
	Returns extra details if checkout is on installments and not fully paid.
	"""

	cache_name = 'checkout_receipt_view'

	# checking for cached
	cached_data = get_cache(cache_name, pk=reference)
	if cached_data:
		return Response(cached_data, status=status.HTTP_200_OK)

	try:
		# Try fetching by checkoutID first
		checkout = Checkout.objects.get(checkoutID=reference)
		installment = None
	except Checkout.DoesNotExist:
		# If not found, try by installment reference
		try:
			installment = InstallmentPayment.objects.get(reference=reference)
			checkout = installment.checkout
		except InstallmentPayment.DoesNotExist:
			return Response(
				{"status": "error", "message": "Checkout/Installment not found."},
				status=status.HTTP_404_NOT_FOUND
			)

	# Base checkout serialization
	data = ReceiptCheckoutReceiptSerializer(checkout).data

	# If installment payment method, calculate progress
	if checkout.payment_method == "installmental_payment":
		total_paid = checkout.total_paid()
		remaining_balance = checkout.total_amount - total_paid
		if remaining_balance < 0:
			remaining_balance = 0

		# Add installment-specific info
		data["installment_info"] = {
			"total_paid": total_paid,
			"remaining_balance": remaining_balance,
			"is_fully_paid": remaining_balance == 0,
			"installments_count": checkout.rn_installments.count(),
			"last_payment_reference": installment.reference if installment else None
		}

	# set cache
	set_cache(cache_name, reference, data)

	return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def verify_paystack_payment(request, reference=None):
	# reference = request.query_params.get("reference")

	if not reference:
		return Response({"status": "error", "message": "Reference is required"}, status=status.HTTP_400_BAD_REQUEST)

	# First check if this payment was already processed by webhook
	try:
		print("Trying to find checkout by checkoutID...")
		checkout = Checkout.objects.get(checkoutID=reference)
		print(f"Found checkout with ID: {checkout.id}")
		if checkout.payment_status == "completed":
			print("Payment already completed, returning status.")
			return checkout_status_fxn(reference)
	except Checkout.DoesNotExist:
		print("Checkout not found by checkoutID, verifying with paystack...")
		checkout = None

	print(f'DEBUG mode: {settings.DEBUG}')
	if settings.DEBUG:
		print("Production mode: skipping manual Paystack verification.")
		return checkout_status_fxn(reference)
	else:
		print("Development mode: proceeding with manual Paystack verification.")
		return checkout_status_fxn(reference)

	# return checkout_status_fxn(reference)
	# If not yet verified, query Paystack’s verify endpoint
	headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
	url = f"https://api.paystack.co/transaction/verify/{reference}"

	response = requests.get(url, headers=headers)
	data = response.json()
	print("Paystack verification response:")
	print(f'data: {data}')

	if not data.get("status"):
		print("Verification failed or invalid reference.")
		return Response({"status": "error", "message": data.get("message")}, status=status.HTTP_400_BAD_REQUEST)

	verification_data = data["data"]
	print("Verification data:")
	print(f'verification_data: {verification_data}')
	event_status = verification_data.get("status")
	print(f"Event status: {event_status}")

	if event_status == "success":
		print("Payment successful, processing...")
		# Try to find checkout or installment again (in case webhook missed)
		metadata = verification_data.get("metadata", {})
		checkoutHexID = metadata.get("checkoutHexID") if metadata else None
		print(f"checkoutHexID from metadata: {checkoutHexID}")

		if not checkout:
			print("Trying to find checkout by checkoutHexID from metadata...")
			checkout = (
				Checkout.objects.filter(checkoutID=checkoutHexID).first()
				or Checkout.objects.filter(checkoutID=reference).first()
			)

		if not checkout:
			print("Checkout not found...")
			return Response({"status": "error", "message": "Checkout not found"}, status=status.HTTP_404_NOT_FOUND)

		result = process_successful_payment(checkout, verification_data)
		return result

	elif event_status == "failed":
		result = process_failed_payment(checkout, data)
		return result
	print("Event not specifically handled, ignoring.")
	return Response({"status": "ignored", "message": f"Unhandled event {event_status}"}, status=status.HTTP_200_OK)


@permission_classes([AllowAny])
def verify_paystack_signature(request):
	"""
	Verify that the request came from Paystack using the signature.
	"""
	signature = request.body
	print(''.rjust(30, '0'))
	print(f'request body:')
	print(f'signature: {signature}')
	paystack_signature = request.headers.get("X-Paystack-Signature", "")
	computed_signature = hmac.new(
		settings.PAYSTACK_SECRET_KEY.encode("utf-8"),
		msg=signature,
		digestmod=hashlib.sha512
	).hexdigest()
	return hmac.compare_digest(computed_signature, paystack_signature)

@api_view(['POST'])
@permission_classes([AllowAny])  # Paystack is external, so allow unauthenticated
def paystack_webhook(request):
	# Step 1: Validate signature
	if not verify_paystack_signature(request):
		return Response({"status": "error", "message": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)

	# Step 2: Parse JSON payload
	payload = json.loads(request.body)
	print(''.rjust(30, '1'))
	print(f'payload: {payload}')
	event = payload.get("event")
	print(''.rjust(30, '2'))
	print(f'event: {event}')
	data = payload.get("data", {})
	print(''.rjust(30, '3'))
	print(f'data: {data}')
	reference = data.get("reference")
	print(''.rjust(30, '4'))
	print(f'reference: {reference}')
	metadata = data.get("metadata", {})
	print(''.rjust(30, 'e'))
	print(f'metadata: {metadata}')
	checkoutHexID = metadata.get("checkoutHexID") if metadata else None

	print(f"Received webhook for event: {event}, reference: {reference}, checkoutHexID: {checkoutHexID}")

	# Try to find checkout by checkoutID first
	try:
		print("Trying to find checkout by checkoutID...")
		checkout = Checkout.objects.get(checkoutID=reference)
		print(''.rjust(30, '5'))
		print(f"Found checkout with ID: {checkout.id}")
	except Checkout.DoesNotExist:
		# If not found, try by checkoutHexID from metadata
		print("Checkout not found by checkoutID, trying checkoutHexID from metadata...")
		try:
			print("Fetching by checkoutHexID...")
			checkout = Checkout.objects.get(checkoutID=checkoutHexID)
			print(''.rjust(30, 'f'))
			print(f"Found checkout with ID: {checkout.id} using checkoutHexID")
		except checkout.DoesNotExist:
			# Try by installment reference
			print("Checkout not found, trying installment reference...")
			try:
				print("Fetching by installment reference...")
				installment = Checkout.rn_installments.get(reference=reference)
				print(''.rjust(30, '6'))
				print(f"Found installment with ID: {installment.id}")
				checkout = installment.checkout
				print(''.rjust(30, '7'))
				print(f"Associated checkout ID: {checkout.id}")
			except:
				print(''.rjust(30, '8'))
				print('Checkout/Installment not found.')
				return Response({"status": "error", "message": "Checkout/Installment not found."}, status=status.HTTP_404_NOT_FOUND)


	# Step 3: Handle successful payments
	if event == "charge.success":
		result = process_successful_payment(checkout, data)
		return result

	# Step 5: Handle other events if needed
	elif event == "charge.failed":
		result = process_failed_payment(checkout, data)
		return result

	print("Event not specifically handled, ignoring.")
	return Response({"status": "ignored", "message": f"Unhandled event {event}"}, status=status.HTTP_200_OK)

@api_view(['GET'])
def checkout_status(request, reference):
	return checkout_status_fxn(reference)

@api_view(['GET'])
def installment_payment(request, reference):
	"""
		Fetch checkout receipt data by checkoutID or installment reference.
		Returns extra details if checkout is on installments and fully or not fully paid.
	"""
	try:
		# Try fetching by checkoutID first
		print(f"Fetching installment payment for reference: {reference}")
		checkout = Checkout.objects.prefetch_related("rn_installments").get(checkoutID=reference)
		installment = checkout.rn_installments.order_by("-id").first()  # last installment
		print(f'Found checkout with ID: {checkout.id}')
	except Checkout.DoesNotExist:
		# # If not found, try by installment reference
		print(f"Checkout with reference: {reference} not found.")
		return Response(
			{"status": "error", "message": "Checkout not found."},
			status=status.HTTP_404_NOT_FOUND
		)

	# Base checkout serialization
	data = ReceiptCheckoutReceiptSerializer(checkout).data
	print("Base checkout data:")
	print(f'data: {data}')

	# If installment payment method, calculate progress
	if checkout.payment_method == "installmental_payment":
		print("Installmental payment method confirmed, calculating progress...")
		total_paid = checkout.total_paid()
		print(f"Total paid so far: {total_paid}")
		remaining_balance = checkout.total_amount - total_paid
		print(f"Remaining balance: {remaining_balance}")
		if remaining_balance < 0:
			print("Overpayment detected, adjusting remaining balance to 0")
			remaining_balance = 0

		print(f'installment count: {checkout.rn_installments.count()}')

		# Add installment-specific info
		data["total_paid"] = str(total_paid)
		data["remaining_balance"] = str(remaining_balance)
		data["is_fully_paid"] = remaining_balance == 0
		data["installments_count"] = checkout.rn_installments.count()
		data["last_payment_reference"] = installment.reference if installment else None
		data["new_payment_details"] = {
			'reference': checkout.payment_method, # continue here
			'checkout_id': checkout.id,
			'amount': int(remaining_balance),  # convert to kobo
			'email': checkout.email,
			'checkout_reference': checkout.checkoutID.hex,
		}
		print("Final data with installment info:")
		print(f'data: {data}')

	return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_unfulfilled_checkout_ids(request, pk):
	print(f"Received request to fetch unfulfilled checkout IDs for user ID: {pk}")
	if request.method == 'GET':
		print(f"Fetching unfulfilled checkout IDs for user ID: {pk}")
		user = User.objects.get(pk=pk)
		print(f"Found user: {user.email}")
		pending_checkouts = Checkout.objects.filter(
			user=user,
			payment_method="installmental_payment",
			payment_status="pending"
		).values_list("checkoutID", flat=True)
		print(f"Pending checkouts found:")
		[print(f"	- {checkout_id}") for checkout_id in list(pending_checkouts)]
		# print(f'list(pending_checkouts): {list(pending_checkouts)}')
		data = {
			"id": user.id,
			"email": user.email,
			"has_unfulfilled_installments": pending_checkouts.exists(),
			"unfulfilled_checkout_ids": list(pending_checkouts),
		}
		print(f'data: {data}')
		return Response(data, status=status.HTTP_200_OK)
	return Response({"message": "Invalid request method."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['GET'])
def has_unfulfilled_installments(request, pk):
	print(f"Received request to check if unfulfilled installments for user ID: {pk}")
	if request.method == 'GET':
		print(f"checking for unfulfilled installments for user ID: {pk}")
		user = User.objects.get(pk=pk)
		print(f"Found user: {user.email}")
		pending_checkouts = Checkout.objects.filter(
			user=user,
			payment_method="installmental_payment",
			payment_status="pending"
		).exists()
		print(f"Pending checkouts found: {pending_checkouts}")

		# print(f'data: {data}')
		return Response(pending_checkouts, status=status.HTTP_200_OK)
	return Response({"message": "Invalid request method."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


# All known Paystack webhook events (as of 2025)
PAYSTACK_EVENTS = {
	# Payments & Charges
	"charge.success",
	"charge.failed",
	"charge.dispute.create",
	"charge.dispute.remind",
	"charge.dispute.resolve",

	# Customers & Verification
	"customeridentification.success",
	"customeridentification.failed",

	# Transfers
	"transfer.success",
	"transfer.failed",
	"transfer.reversed",

	# Dedicated Virtual Accounts
	"dedicatedaccount.assign.success",
	"dedicatedaccount.assign.failed",

	# Invoices
	"invoice.create",
	"invoice.update",
	"invoice.failed",
	"invoice.payment_failed",

	# Subscriptions
	"subscription.create",
	"subscription.disable",
	"subscription.not_renewing",
	"subscription.expiring_card",

	# Refunds
	"refund.pending",
	"refund.processing",
	"refund.processed",
	"refund.failed",

	# Payment Requests
	"paymentrequest.pending",
	"paymentrequest.success",
	"paymentrequest.failed",
}