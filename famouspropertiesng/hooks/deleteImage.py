import requests
from django.http import JsonResponse
import json
from django.conf import settings

def delete_image(request, classObject):
    print("delete_image called with classObject:", classObject.__name__)
    if request.method == "POST":
        data = json.loads(request.body)
        file_id = data.get("fileId")
        print(f"Received request to delete image with fileId: {file_id}")

        if not file_id:
            return JsonResponse({"error": "fileId required"}, status=400)

        # Call ImageKit delete API
        url = "https://api.imagekit.io/v1/files/" + file_id
        response = requests.delete(
            url,
            auth=(settings.IMAGEKIT_PRIVATE_KEY, "")  # Private key is required for deletion
        )
        
        print(f"ImageKit response status code: {response.status_code}")

        if response.status_code == 204:
            classObject.objects.filter(fileId=file_id).delete()
            return JsonResponse({"message": "Image deleted successfully"})
        else:
            try:
                details = response.json()
            except ValueError:
                details = response.text  # fallback if no JSON
            return JsonResponse(
                {"error": "Failed to delete from ImageKit", "details": details},
                status=500,
            )
    return JsonResponse({"error": "Only POST allowed"}, status=405)
