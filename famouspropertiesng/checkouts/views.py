from django.shortcuts import render, get_list_or_404, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import Checkout, CheckoutProduct, InstallmentPayment
from products.models import Product
from hooks.prettyprint import pretty_print_json
import json, requests, uuid, hmac, hashlib
from django.conf import settings
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .serializers import CheckoutSerializer, CheckoutProductSerializer
from .serializers import InstallmentPaymentSerializer, ReceiptCheckoutReceiptSerializer
from .serializers import ReceiptCheckoutProductSerializer, ReceiptInstallmentPaymentSerializer
from users.models import User

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

def getSK():
	response = requests.get('https://dafetiteapiendpoint.pythonanywhere.com/get-paystack-keys/sk/')
	result = response.json()
	# print(f'sk: {result.get("sk")}')
	# print(f"Generated reference: {ref}")
	return result.get("sk")
PAYSTACK_SECRET_KEY = getSK()

# create Paystack customer
def create_paystack_customer(user):
	"""
	Create a Paystack customer for this user (if not already created)
	"""
	if user.paystack_customer_id:
		return user.paystack_customer_id  # already exists

	url = "https://api.paystack.co/customer"
	headers = {
		"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
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
		"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
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

# Create your views here.
@api_view(['GET', 'POST'])
def checkouts(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		print("Received checkout data:")
		pretty_print_json(data)
		cleaned_data = {key: value for key, value in data.items() if key in valid_fields}
		for frontend_key, backend_key in field_mapping.items():
			cleaned_data[backend_key] = data.get(frontend_key)
		userID = data.get('userID', None)
		pod = data.get('paymentMethod', None) == "pay_on_delivery"
		instllPay = data.get('paymentMethod', None) == "installmental_payment"
		print(f"userID: {userID}, pod: {pod}. installmental_payment: {instllPay}")
		print("Cleaned data:")
		pretty_print_json(cleaned_data)

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
		# pretty_print_json(serialized_checkout)
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

# @api_view(['GET'])
# def generate_reference(request):
# 	print(f'the pkey: {PAYSTACK_SECRET_KEY}')
# 	return Response({'a':8}, status=status.HTTP_200_OK)
# @api_view(['POST'])
# def verify_payment(request):
# 	if request.method == "POST":
# 		body = json.loads(request.body)
# 		reference = body.get("reference")
# 		print(f"Verifying payment for reference: {reference}")
# 		pretty_print_json(body)
# 		# checkout_id = body.get("checkout_id")

# 		headers = {
# 			"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",  # your test secret key
# 			"Content-Type": "application/json",
# 		}
# 		url = f"https://api.paystack.co/transaction/verify/{reference}"

# 		response = requests.get(url, headers=headers)
# 		result = response.json()

# 		print(f'Paystack response for reference {reference}:')
# 		pretty_print_json(result)
# 		if not result.get("status"):
# 			print("Paystack API request failed")
# 			return Response({
# 					"status": "error",
# 					"message": "Paystack API request failed",
# 					"data": result
# 				}
# 				, status=status.HTTP_400_BAD_REQUEST)

# 		data = result.get("data", {})
# 		if data.get("status") != "success":
# 			print("Payment verification failed or payment not successful")
# 			return Response({
# 					"status": "failed",
# 					"message": "Payment verification failed or payment not successful",
# 					"data": result
# 				},
# 				status=status.HTTP_400_BAD_REQUEST)

# 		amount = Decimal(data["amount"]) / 100  # Paystack returns in kobo
# 		transaction_id = data.get("id")

# 		try:
# 			checkout = Checkout.objects.get(checkoutID=reference)
# 		except Checkout.DoesNotExist:
# 			print("Checkout not found")
# 			return Response({
# 					"status": "error",
# 					"message": "Checkout not found"
# 				},
# 				status=status.HTTP_404_NOT_FOUND)

# 		# # detect overpayment
# 		# if amount > checkout.remaining_balance:
# 		# 	print("Overpayment detected")
# 		# 	# return Response(
# 		# 	# 	{"status": "error", "message": "Overpayment detected"},
# 		# 	# 	status=status.HTTP_400_BAD_REQUEST
# 		# 	# )

# 		if checkout.payment_method == "installment":
# 			# detect overpayment
# 			if amount > checkout.remaining_balance:
# 				print("Overpayment detected")
# 				# return Response(
# 				# 	{"status": "error", "message": "Overpayment detected"},
# 				# 	status=status.HTTP_400_BAD_REQUEST
# 				# )

# 			# Create a new installment record
# 			# installment = checkout.record_installment(reference, amount, transaction_id, data.get("receipt_url"))
# 			# try:
# 			installment = checkout.record_installment(reference, amount, transaction_id)
# 			# except IntegrityError:
# 				# print("Overpayment detected confirmed")
# 				# return Response(
# 				# 	{"status": "error", "message": "Overpayment detected"},
# 				# 	status=status.HTTP_400_BAD_REQUEST
# 				# )

# 			serialized_installment = InstallmentPaymentSerializer(installment).data
# 			serialized_checkout = CheckoutSerializer(checkout).data
# 			print(f"Recorded installment: {installment.id} for checkout: {checkout.id}")
# 			pretty_print_json(serialized_installment)
# 			print('checkout:')
# 			pretty_print_json(serialized_checkout)

# 			return Response({
# 					"status": "success",
# 					"message": "Installment recorded",
# 					"total_paid": checkout.total_paid(),
# 					"receipt_url": checkout.receipt_url
# 				}, status=status.HTTP_200_OK)

# 		else:
# 				# pay now (One-off payment)
# 				checkout.remaining_balance = 0
# 				checkout.payment_status = "completed"
# 				checkout.transaction_id = transaction_id
# 				# checkout.receipt_url = data.get("receipt_url")
# 				checkout.save()

# 				serialized_checkout = CheckoutSerializer(checkout).data
# 				print('checkout:')
# 				pretty_print_json(serialized_checkout)

# 				return Response({
# 						"status": "success",
# 						"message": "Payment verified successfully",
# 						"receipt_url": checkout.receipt_url
# 					},
# 					status=status.HTTP_200_OK)

# 		# if result.get("data", {}).get("status") == "success":
# 		# 	return JsonResponse({"status": "success", "data": result["data"]})

# 		# return Response({"status": "failed", "data": result}, status=status.HTTP_400_BAD_REQUEST)
# 	return Response({"message": "Invalid request method."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
def checkout_receipt_view(request, reference):
	"""
	Fetch checkout receipt data by checkoutID or installment reference.
	Returns extra details if checkout is on installments and not fully paid.
	"""
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

	return Response(data, status=status.HTTP_200_OK)
# Customer info (first_name, last_name, email, etc.)

# Checkout/order details (subtotal_amount, shipping_fee, total_amount, remaining_balance)

# Product list (CheckoutProduct related objects)

# Payment details (payment_method, transaction_id, status)

# Installment history (if applicable)

# Replace with your own Paystack secret key

def verify_paystack_signature(request):
	"""
	Verify that the request came from Paystack using the signature.
	"""
	signature = request.body
	print(''.rjust(30, '0'))
	print(f'request body:')
	pretty_print_json(json.loads(signature))
	paystack_signature = request.headers.get("X-Paystack-Signature", "")
	computed_signature = hmac.new(
		PAYSTACK_SECRET_KEY.encode("utf-8"),
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
	pretty_print_json(payload)
	event = payload.get("event")
	print(''.rjust(30, '2'))
	print(f'event: {event}')
	data = payload.get("data", {})
	print(''.rjust(30, '3'))
	pretty_print_json(data)
	reference = data.get("reference")
	print(''.rjust(30, '4'))
	print(f'reference: {reference}')
	metadata = data.get("metadata", {})
	print(''.rjust(30, 'e'))
	pretty_print_json(metadata)
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
		print("Processing charge.success event")
		amount = Decimal(data.get("amount", 0)) / 100  # Paystack returns in kobo
		transaction_id = data.get("id")
		payment_channel = data.get("channel")  # e.g., card, bank, etc.

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

			return Response({
				"status": "success",
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

			serialized_checkout = CheckoutSerializer(checkout).data
			print(''.rjust(30, 'c'))
			print('checkout:')
			# pretty_print_json(serialized_checkout)

			return Response({
				"status": "success",
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

			return Response({
				"status": "success",
				"message": "Pay on Delivery (via transfer) confirmed",
				"receipt_url": checkout.receipt_url
			}, status=status.HTTP_200_OK)

	# Step 5: Handle other events if needed
	elif event == "charge.failed":
		print("Processing charge.failed event")
		checkout.payment_status = "failed"
		print('changed payment_status to failed')
		checkout.save()

		try:
			print("Trying to update installment status to failed...")
			installment = InstallmentPayment.objects.get(reference=reference)
			installment.styesatus = "failed"
			installment.save()
			print("Installment status updated to failed.")
		except InstallmentPayment.DoesNotExist:
			print("No associated installment found, skipping installment update.")
			pass

		return Response({
			"status": "error",
			"message": "Payment failed"
		}, status=status.HTTP_200_OK)
	print("Event not specifically handled, ignoring.")
	return Response({"status": "ignored", "message": f"Unhandled event {event}"}, status=status.HTTP_200_OK)

@api_view(['GET'])
def checkout_status(request, reference):
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
			installment = InstallmentPayment.objects.get(reference=reference)
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
	return Response(response_data, status=status.HTTP_200_OK)

@api_view(['GET'])
def installment_payment(request, reference):
	try:
		# Try fetching by checkoutID first
		print(f"Fetching installment payment for reference: {reference}")
		checkout = Checkout.objects.prefetch_related("rn_installments").get(checkoutID=reference)
		installment = checkout.rn_installments.order_by("-id").first()  # last installment
		print(f'Found checkout with ID: {checkout.id}')
	except Checkout.DoesNotExist:
		# # If not found, try by installment reference
		# print("Checkout not found, trying installment reference...")
		# try:
		# 	print("Fetching by installment reference...")
		# 	installment = InstallmentPayment.objects.get(reference=reference)
		# 	checkout = installment.checkout
		# 	print(f"Found installment with ID: {installment.id} for checkout ID: {checkout.id}")
		# except InstallmentPayment.DoesNotExist:
		print(f"Checkout with reference: {reference} not found.")
		return Response(
			{"status": "error", "message": "Checkout not found."},
			status=status.HTTP_404_NOT_FOUND
		)

	# Base checkout serialization
	data = ReceiptCheckoutReceiptSerializer(checkout).data
	print("Base checkout data:")
	# pretty_print_json(data)

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

		# Add installment-specific info
		# data["installment_info"] = {
		# 	# "total_paid": total_paid,
		# 	# "remaining_balance": remaining_balance,
		# 	# "is_fully_paid": remaining_balance == 0,
		# 	# "installments_count": checkout.rn_installments.count(),
		# 	"last_payment_reference": installment.reference if installment else None
		# }

		new_payment_reference = str(uuid.uuid4()).replace("-", "")

		print(f'installment count: {checkout.rn_installments.count()}')

		# Add installment-specific info
		data["total_paid"] = str(total_paid)
		data["remaining_balance"] = str(remaining_balance)
		data["is_fully_paid"] = remaining_balance == 0
		data["installments_count"] = checkout.rn_installments.count()
		data["last_payment_reference"] = installment.reference if installment else None
		data["new_payment_details"] = {
			'reference': new_payment_reference,
			'checkout_id': checkout.id,
			'amount': int(remaining_balance),  # convert to kobo
			'email': checkout.email,
			'checkout_reference': checkout.checkoutID.hex,
		}
		print("Final data with installment info:")
		# pretty_print_json(data)

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
		# pretty_print_json(list(pending_checkouts))
		data = {
			"id": user.id,
			"email": user.email,
			"has_unfulfilled_installments": pending_checkouts.exists(),
			"unfulfilled_checkout_ids": list(pending_checkouts),
		}
		# pretty_print_json(data)
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
		# [print(f"	- {checkout_id}") for checkout_id in list(pending_checkouts)]
		# pretty_print_json(list(pending_checkouts))
		# data = {
		# 	"id": user.id,
		# 	"email": user.email,
		# 	"has_unfulfilled_installments": pending_checkouts.exists(),
		# 	"unfulfilled_checkout_ids": list(pending_checkouts),
		# }
		# pretty_print_json(data)
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