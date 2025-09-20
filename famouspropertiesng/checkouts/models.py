from django.db import models
import uuid
from django.db import models, IntegrityError, transaction

# Create your models here.
class Checkout(models.Model):
	checkoutID = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Checkout {self.id}"