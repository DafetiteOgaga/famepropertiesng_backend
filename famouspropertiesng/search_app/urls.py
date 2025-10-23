from django.urls import path
from . import views

app_name = "search_app"

urlpatterns = [
	# Create your urlpatterns here.
	path("check-email/<str:email>/", views.check_email, name="check_email"),
	path('store/check-store-name/<str:name>/', views.check_store_name, name='check_store_name'),  # For checking store name availability
	path('store/check-store-email/<str:email>/', views.check_store_email, name='check_store_email'),  # For checking store email availability
	path('search/<int:pk>/<str:s_text>/', views.search_data, name='search_data'),  # For searching products
]
