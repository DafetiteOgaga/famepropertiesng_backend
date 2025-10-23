from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import StaffFCMToken
from hooks.prettyprint import pretty_print_json
from hooks.cache_helpers import clear_key_and_list_in_cache
from .firebase_setup.firebase_notification_utils import send_warmup_notification
from django.db import OperationalError
from time import sleep

cache_name = 'staff_fcm_tokens'

@api_view(["POST"])
def register_fcm_token(request):
	pretty_print_json(request.data)
	token = request.data.get("fcm_token")
	device_info = request.data.get("device_info")
	print(f"Received FCM token: {token} for device: {device_info['device_id'] if device_info else 'N/A'}")
	pretty_print_json(device_info)
	print(f"From user: {request.user}")

	if not token or not device_info:
		return Response({"error": "FCM token and device_info are required"}, status=400)

	# Try a few times in case of temporary lock
	for attempt in range(3):
		print(f"Attempt {attempt + 1} to save token...")
		try:
			print("Accessing database...")
			# 🔹 1. Find existing record for this user + device
			print(f"Checking for existing entry with device_id: {device_info['device_id']} ...")
			existing_entry = StaffFCMToken.objects.filter(user=request.user, device_id=device_info["device_id"]).first()

			if existing_entry:
				print("Existing entry found.")
				if existing_entry.fcm_token != token:
					# ✅ Device exists but token changed → update it
					print(f"🔁 Token refreshed for {request.user} on {device_info['device_id']}")
					existing_entry.fcm_token = token
					for field, value in device_info.items():
						if hasattr(existing_entry, field):  # only set fields that exist in model
							print(f" - Updating {field} to {value}")
							setattr(existing_entry, field, value)

					print("Saving updated entry...")
					existing_entry.save()
				else:
					print(f"⚠️ Token already up-to-date for {request.user} on {device_info['device_id']}")
			else:
				print("No existing entry found.")
				# ✅ New device for this user → create a new record
				created_new = StaffFCMToken.objects.create(user=request.user, fcm_token=token, **device_info)
				print("New entry created.")
				print(f"✅ New device registered for {created_new.user.first_name}: {created_new.device_id}")

			# 🔹 Clear cache to refresh token list
			clear_key_and_list_in_cache(key=cache_name)

			# 🔹 Warm-up notification (optional)
			send_warmup_notification(token)

			return Response({"message": "Token registered successfully"})

		except OperationalError:
			print("Database locked, retrying...")
			sleep(0.5)

	return Response({"error": "Database locked, could not save token"}, status=500)
