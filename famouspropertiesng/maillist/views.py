from django.shortcuts import render
from django.shortcuts import render, get_list_or_404, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import *
from .serializers import MailListSerializer, ResponseMailListSerializer

# Create your views here.
@api_view(['GET', 'POST'])
def maillist(request, pk=None):
	if request.method == 'POST':
		email = request.data.get('email')
		if email:
			if not MailList.objects.filter(email=email).exists():
				maillist_entry = MailList(email=email)
				maillist_entry.save()
				return Response({"message": "Email added to the mailing list."}, status=status.HTTP_201_CREATED)
			else:
				return Response({"message": "Email already exists in the mailing list."}, status=status.HTTP_200_OK)
		else:
			return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
	else:
		if pk:
			entry = MailList.objects.filter(pk=pk)
			if not entry.exists():
				return Response({"error": "MailList entry not found."}, status=status.HTTP_404_NOT_FOUND)
			entry_data = ResponseMailListSerializer(entry.first()).data
			return Response(entry_data, status=status.HTTP_200_OK)
		else:
			maillist_entries = MailList.objects.all()
			emails = ResponseMailListSerializer(maillist_entries, many=True).data
			return Response({"maillist": emails}, status=status.HTTP_200_OK)
