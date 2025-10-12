from rest_framework.response import Response
from rest_framework import status

def is_staff(request):
	if not request.user.is_staff:
		print("User is not staff.")
		return Response({"error": "Only staff can create carousels."}, status=status.HTTP_403_FORBIDDEN)
	print("User is staff.")

