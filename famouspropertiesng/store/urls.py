from django.urls import path
from . import views

app_name = "store"

urlpatterns = [
	# Create your urlpatterns here.
	path('<int:pk>/', views.store_view, name='store_list_create'),  # For creating and listing stores
	path('update-store/<int:pk>/', views.update_store, name='update_store'),  # For updating a store
]
