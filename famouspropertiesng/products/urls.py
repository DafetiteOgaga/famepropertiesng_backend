from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
	# Create your urlpatterns here.
	path("products/", views.products, name="product_list_create"),
	path("products/<int:pk>/", views.products, name="product_list_create"),
	path("products/<str:all>/", views.products, name="product_list_all"),
	path("update-product/<int:pk>/", views.updateProduct, name="update_product"),
	path("delete-products/", views.deleteProduct, name="delete_product"),
	# path("sold-products/<int:pk>/", views.designateAsSold, name="sold_product"),
	path("like-product/<int:pk>/", views.likeProduct, name="like_product"),
	path("store-products/<int:pk>/", views.storeProducts, name="store_products"),
	path('categories/', views.get_categories, name='category_list'),  # For listing categories
	path('category/<str:category>/', views.query_category, name='category_detail'),  # For single category details
	path("available-totals/", views.getAvailableTotal, name="getAvailableTotal")
]
