from django.urls import path
from . import views

app_name = "maillist"

urlpatterns = [
	# Create your urlpatterns here.
	path('', view=views.maillist, name='maillist'),
	path('<int:pk>/', view=views.maillist, name='maillistDetail'),
	# path('all-maillists/', view=views.allMaillists, name='allMaillists'),
]
