import requests
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
import json
from django.conf import settings
from .cache_helpers import clear_key_and_list_in_cache

def delete_object_and_image(request, classObject, cache_name):
	print("delete_object_and_image called with classObject:", classObject.__name__)
	if request.method == "POST":
		data = json.loads(request.body)
		file_id = data.get("fileId")
		print(f"Received request to delete image with fileId: {file_id}")

		if not file_id:
			return Response({"error": "fileId required"}, status=status.HTTP_400_BAD_REQUEST)

		custom_request = data.get("custom_request", False)

		# Call ImageKit delete API
		url = "https://api.imagekit.io/v1/files/" + file_id
		response = requests.delete(
			url,
			auth=(settings.IMAGEKIT_PRIVATE_KEY, "")  # Private key is required for deletion
		)

		print(f"ImageKit response status code: {response.status_code}")

		if response.status_code == 204:
			if not custom_request:
				print("Image deleted from ImageKit, now deleting local objects...")
				deleted_objects = classObject.objects.filter(fileId=file_id)
				deleted_object_ids = [del_object.id for del_object in deleted_objects]
				print(f"Deleted object IDs: {deleted_object_ids}")
				deleted_objects.delete()

				# Invalidate cache
				for idx in deleted_object_ids:
					clear_key_and_list_in_cache(key=cache_name, id=idx)

				return Response({"message": "Image deleted successfully"})
			else:
				deleted_object = classObject.objects.filter(fileId=file_id).first()
				print(f"Deleted object found: {deleted_object}")
				if deleted_object:
					print(f"Deleted object with id: {deleted_object.id}")
					deleted_object.delete()
				else:
					print("No matching object found.")
				clear_key_and_list_in_cache(key=cache_name)
				return True
		else:
			try:
				details = response.json()
			except ValueError:
				details = response.text  # fallback if no JSON
			return Response(
				{"error": "Failed to delete from ImageKit", "details": details},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR,
			)
	return Response({"error": "Only POST allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
