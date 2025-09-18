from django.urls import path
from . import views

app_name = "checkouts"

urlpatterns = [
	# Create your urlpatterns here.
	path('checkouts/', views.checkouts, name='checkouts'),
]
