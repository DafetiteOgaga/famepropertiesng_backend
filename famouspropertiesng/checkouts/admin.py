from django.contrib import admin
from .models import Checkout, CheckoutProduct, InstallmentPayment

# Register your models here.
admin.site.register(Checkout)
admin.site.register(CheckoutProduct)
admin.site.register(InstallmentPayment)
