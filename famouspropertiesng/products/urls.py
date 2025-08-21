from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
	# Create your urlpatterns here.
	path("products/", views.products, name="product_list_create"),
	path("products/<int:pk>/", views.products, name="product_list_create"),
	path("delete-products/", views.deleteProduct, name="delete_product"),
	path("sold-products/<int:pk>/", views.designateAsSold, name="sold_product"),
]
