from django.urls import path
from . import views

app_name = "carousels"

urlpatterns = [
	# Create your urlpatterns here.
	path("carousels/", views.carousels, name="carousel_list_create"),
	path("delete-carousel/", views.deleteCarousel, name="carousel_list_create"),
]
