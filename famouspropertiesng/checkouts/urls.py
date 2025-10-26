from django.urls import path
from . import views

app_name = "checkouts"

urlpatterns = [
	# Create your urlpatterns here.
	path('checkouts/', views.checkouts, name='checkouts'),
	path('checkout/<str:checkoutId>/', views.checkouts, name='checkout'),
	path('update-checkout/<int:pk>/<checkoutID>/', views.update_checkout, name='update-checkout'),
	path('verify-payment/<str:reference>/', views.verify_paystack_payment, name='verify-payment'),
	path('generate-reference/', views.generate_reference, name="generate_reference"),
	path("receipt/<str:reference>/", views.checkout_receipt_view, name="receipt"),
	path("fetch-chechout-details/<str:reference>/", views.fetch_checkout_details, name="receipt"),
	path("paystack-webhook/", views.paystack_webhook, name="paystack_webhook"),
	path('checkout-status/<str:reference>/', views.checkout_status, name='checkout-status'),
	path("get-unfulfilled-and-or-unsettled-checkout-ids/<int:pk>/<str:type>/", views.get_unfulfilled_checkout_ids, name="get-unfulfilled-checkout-ids"),
	path("has-unfulfilled-and-or-unsettled/<int:pk>/", views.has_unfulfilled_installments_and_or_unsettled_delivery_payments, name="has-unfulfilled-and-or-unsettled"),
	path('all-unfulfilled-checkouts/<int:pk>/', views.incomplete_checkouts_ids, name='incomplete-checkouts'),
	# path("get-unsettled-checkout-ids/<int:pk>/", views.get_unfulfilled_checkout_ids, name="get-unsettled-checkout-ids"),
	path("ch/", views.ch, name="ch")
]
