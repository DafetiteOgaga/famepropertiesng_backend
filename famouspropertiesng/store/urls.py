from django.urls import path
from . import views

app_name = "store"

urlpatterns = [
	# Create your urlpatterns here.
	path('<int:pk>/', views.store_view, name='store_list_create'),  # For creating and listing stores
	path('check-store-name/<str:name>/', views.check_store_name, name='check_store_name'),  # For checking store name availability
	path('check-store-email/<str:email>/', views.check_store_email, name='check_store_email'),  # For checking store email availability
]
