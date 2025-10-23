from django.db import models
from django.db.models import Avg

# Store Status
STORE_STATUS_CHOICES = [
	("active", "Active"),
	("suspended", "Suspended"),
	("terminated", "Terminated"),
]

# Create your models here.
class Store(models.Model):
    # Each store is linked to a user (owner)
	# user = models.OneToOneField(
	# 	'users.User',                  # Link to Extended User model
	# 	on_delete=models.CASCADE,      # If user is deleted, store is deleted
	# 	related_name="rn_store",       # Access with user.store
	# 	null=True, # remove later      # A store can exist without a user
	# )

	# change to ForeignKey to temporarily allow multiple stores per user
	user = models.ForeignKey(
		'users.User',                  # Link to Extended User model
		on_delete=models.CASCADE,      # If user is deleted, store is deleted
		related_name="rn_store",       # Access with user.store
		null=True, # remove later      # A store can exist without a user
	)
	store_name = models.CharField(max_length=255, unique=True, db_index=True)  # Unique store identity
	description = models.TextField(blank=True, null=True)       # About the store

	# # Contact Info
	store_phone_number = models.CharField(max_length=20, blank=True, null=True)
	store_email_address = models.EmailField(db_index=True, blank=True, null=True)
	store_address = models.TextField(blank=True, null=True)           # Physical address
	nearest_bus_stop = models.CharField(max_length=200, null=True, blank=True)

	# # Branding
	image_url = models.URLField(blank=True, null=True)  # only store ImageKit URL
	fileId = models.CharField(max_length=200, null=True, blank=True)  # store ImageKit fileId

	# # Business Info
	business_registration_number = models.CharField(max_length=100, blank=True, null=True)
	tax_identification_number = models.CharField(max_length=100, blank=True, null=True)

	# Store Status
	store_status = models.CharField(
		max_length=20,
		choices=STORE_STATUS_CHOICES,
		default="active"
	)

	# Meta Info
	verified = models.BooleanField(default=False)               # Admin verification
	rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)  # Avg rating

	# Timestamps
	created_at = models.DateTimeField(auto_now_add=True)        # Store creation date
	updated_at = models.DateTimeField(auto_now=True)            # Last update
	is_deleted = models.BooleanField(default=False)            # Soft delete flag

	def __str__(self):
		return self.store_name
