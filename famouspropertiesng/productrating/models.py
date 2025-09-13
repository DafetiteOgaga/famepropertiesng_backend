from django.db import models

# Create your models here.
class ProductRating(models.Model):
	# A user can rate a product only once
	product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='rn_prod_ratings')
	user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='rn_product_ratings')
	store = models.ForeignKey('store.Store', on_delete=models.CASCADE, related_name='rn_store_ratings',
            blank=True, null=True # remove later #
            )
	rating = models.PositiveIntegerField(blank=True, null=True)  # Assuming rating is an integer value
	liked = models.BooleanField(default=False)
	review = models.TextField(blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		# user cannot rate the same product more than once
		constraints = [
			models.UniqueConstraint(fields=['product', 'user'], name='unique_product_user')
		]

	def save(self, *args, **kwargs):
		# auto-sync store from product
		self.store = self.product.store
		super().save(*args, **kwargs)

	def __str__(self):
		return f'{self.product.name} rated by {self.user.first_name}'