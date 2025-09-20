from django.contrib import admin
from .models import Checkout, CheckoutProduct

# Register your models here.
admin.site.register(Checkout)
admin.site.register(CheckoutProduct)
