from django.urls import path
from . import views

app_name = "homepage"

urlpatterns = [
	# Create your urlpatterns here.
	path('', views.home, name='home'),
]
