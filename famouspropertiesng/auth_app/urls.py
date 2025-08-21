from django.urls import path
from . import views

app_name = "auth_app"

urlpatterns = [
	# Create your urlpatterns here.
	path("api/auth/google/", views.google_login, name="google_login"),
	path("api/authenticate/", views.generate_signature, name="generate_signature"),
	path("imagekit-auth/", views.imagekit_auth, name="imagekit_auth"),
	# path("products/", views.products, name="product_list_create"),
]
