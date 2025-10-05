from django.urls import path
from . import views

app_name = "checkouts"

urlpatterns = [
	# Create your urlpatterns here.
	path('checkouts/', views.checkouts, name='checkouts'),
	# path('verify-payment/', views.verify_payment, name='verify-payment'),
	# path('generate-reference/', views.generate_reference, name="generate_reference"),
	path("receipt/<str:reference>/", views.checkout_receipt_view, name="receipt"),
	path("installment-payment/<str:reference>/", views.installment_payment, name="receipt"),
	path("paystack-webhook/", views.paystack_webhook, name="paystack_webhook"),
	path('checkout-status/<str:reference>/', views.checkout_status, name='checkout-status'),
	path("get-unfulfilled-checkout-ids/<int:pk>/", views.get_unfulfilled_checkout_ids, name="get-unfulfilled-checkout-ids"),
	path("has-unfulfilled-installments/<int:pk>/", views.has_unfulfilled_installments, name="has-unfulfilled-installments"),
]
