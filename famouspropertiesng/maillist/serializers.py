from rest_framework import serializers
from .models import *

# Create your serializers here.
class MailListSerializer(serializers.ModelSerializer):
	class Meta:
		model = MailList
		fields = '__all__'  # or list only fields you want

class ResponseMailListSerializer(serializers.ModelSerializer):
	class Meta:
		model = MailList
		fields = ['id', 'email', 'subscribed_at']  # Exclude sensitive fields like password
  