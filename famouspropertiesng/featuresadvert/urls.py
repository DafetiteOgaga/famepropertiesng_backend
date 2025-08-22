from django.urls import path
from . import views

app_name = "featuresadvert"

urlpatterns = [
	# Create your urlpatterns here.
	path("features-adverts/", views.featuresAdvert, name="featuresAdvert_list_create"),
	path("delete-features-adverts/", views.deleteFeaturesAdverts, name="deleteFeaturesAdverts"),
]