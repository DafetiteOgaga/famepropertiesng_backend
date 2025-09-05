from django.urls import path
from . import views

app_name = "productrating"

urlpatterns = [
	# Create your urlpatterns here.
	path("product-rating-create/<int:pk>/", views.productRating, name="productrating_list_create"),
	path("product-ratings/<int:pk>/", views.productRating, name="productrating_list_user"),
	path("product-ratings/", views.productRating, name="productrating_list_all"),
]
