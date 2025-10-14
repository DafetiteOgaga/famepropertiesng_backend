from datetime import datetime
import uuid

def generate_checkout_id():
	"""
	Generates a unique checkout ID combining timestamp and a short UUID segment.
	Example: 20251012145530765432a3f9
	"""
	from .models import Checkout, InstallmentPayment
	while True:
		timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")  # yyyymmddhhmmssµs
		random_part = uuid.uuid4().hex[:10]  # take first 10 hex chars of a UUID
		reference = f"{timestamp}{random_part}"
		print(f"Generated checkout ID: {reference} and length: {len(reference)}")
		is_checkout = Checkout.objects.filter(checkoutID=reference).exists()
		is_installment = InstallmentPayment.objects.filter(reference=reference).exists()
		if not is_checkout and not is_installment:
			print(f"Generated unique reference: {reference}")
			return reference
		print(f"Collision detected for reference: {reference}, regenerating...")