"""
URL configuration for famouspropertiesng project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),  # For featuressadvert configuration
    path('', include('search_app.urls')),     # For search_app configuration
    path('', include('checkouts.urls')),     # For checkouts configuration
    path('store/', include('store.urls')),     # For store configuration
    path('', include('productrating.urls')),     # For productrating configuration
    path('maillist/', include('maillist.urls')),     # For maillist configuration
    path('', include('products.urls')),     # For products configuration
    path('', include('featuresadvert.urls')),     # For featuresadvert configuration
    path('', include('productsadvert.urls')),     # For productsadvert configuration
    path('', include('carousels.urls')),     # For carousels configuration
    path('', include('auth_app.urls')),     # For auth_app configuration
    path('users/', include('users.urls')),     # For users configuration
    path('', include('homepage.urls')),     # For homepage configuration
]
