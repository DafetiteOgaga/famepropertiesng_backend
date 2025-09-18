from django.shortcuts import render, get_list_or_404, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import *
from hooks.prettyprint import pretty_print_json
import json

# Create your views here.
@api_view(['GET', 'POST'])
def checkouts(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		pretty_print_json(data)
		return Response({"message": "POST request received."}, status=status.HTTP_200_OK)
	return Response({"message": "Checkouts endpoint is under construction."}, status=status.HTTP_200_OK)
