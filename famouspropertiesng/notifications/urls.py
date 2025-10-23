from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
	# Create your urlpatterns here.
	path("register-fcm-token/", views.register_fcm_token, name="register_fcm_token"),
]
