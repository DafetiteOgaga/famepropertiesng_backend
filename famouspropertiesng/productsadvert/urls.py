from django.urls import path
from . import views

app_name = "productsadvert"

urlpatterns = [
	# Create your urlpatterns here.
	path("products-adverts/", views.productsAdvert, name="productAdvert_list_create"),
	path("delete-products-adverts/", views.deleteProductsAdvert, name="delete_product_advert"),
]
