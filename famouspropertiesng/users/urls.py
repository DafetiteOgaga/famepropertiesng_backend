from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
	# Create your urlpatterns here.
	path('', view=views.users, name='users'),
    path('<int:pk>/', view=views.users, name='userDetail'),
    # path('all-users/', view=views.allUsers, name='allUsers'),
]
