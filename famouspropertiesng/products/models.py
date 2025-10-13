from django.db import models
from django.db.models import F
from hooks.cache_helpers import clear_key_and_list_in_cache

# fulldesc = """Eos no lorem eirmod diam diam, eos elitr et gubergren diam sea. Consetetur vero aliquyam invidunt duo dolores et duo sit. Vero diam ea vero et dolore rebum, dolor rebum eirmod consetetur invidunt sed sed et, lorem duo et eos elitr, sadipscing kasd ipsum rebum diam. Dolore diam stet rebum sed tempor kasd eirmod. Takimata kasd ipsum accusam sadipscing, eos dolores sit no ut diam consetetur duo justo est, sit sanctus diam tempor aliquyam eirmod nonumy rebum dolor accusam, ipsum kasd eos consetetur at sit rebum, diam kasd invidunt tempor lorem, ipsum lorem elitr sanctus eirmod takimata dolor ea invidunt.
# Dolore magna est eirmod sanctus dolor, amet diam et eirmod et ipsum. Amet dolore tempor consetetur sed lorem dolor sit lorem tempor. Gubergren amet amet labore sadipscing clita clita diam clita. Sea amet et sed ipsum lorem elitr et, amet et labore voluptua sit rebum. Ea erat sed et diam takimata sed justo. Magna takimata justo et amet magna et.
# """
# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    fullDescription = models.TextField()
    marketingDescription = models.TextField(null=True, blank=True)
    marketPrice = models.DecimalField(max_digits=12, decimal_places=2)
    discountPrice = models.DecimalField(max_digits=12, decimal_places=2)
    numberOfItemsAvailable = models.IntegerField(default=1)  # New field for number of items
    thumbnail_url_0 = models.URLField(blank=True, null=True)  # only store ImageKit URL
    image_url_0 = models.URLField(blank=True, null=True)  # only store ImageKit URL
    fileId_0 = models.CharField(max_length=200, null=True, blank=True)  # store ImageKit fileId
    image_url_1 = models.URLField(blank=True, null=True)  # only store ImageKit URL
    fileId_1 = models.CharField(max_length=200, null=True, blank=True)  # store ImageKit fileId
    image_url_2 = models.URLField(blank=True, null=True)  # only store ImageKit URL
    fileId_2 = models.CharField(max_length=200, null=True, blank=True)  # store ImageKit fileId
    image_url_3 = models.URLField(blank=True, null=True)  # only store ImageKit URL
    fileId_3 = models.CharField(max_length=200, null=True, blank=True)  # store ImageKit fileId
    image_url_4 = models.URLField(blank=True, null=True)  # only store ImageKit URL
    fileId_4 = models.CharField(max_length=200, null=True, blank=True)  # store ImageKit fileId
    sold = models.BooleanField(default=False)  # Indicates if the product is sold
    noOfReviewers = models.IntegerField(default=0)
    technicalDescription = models.TextField(null=True, blank=True)
    techFeature_1 = models.CharField(max_length=200, null=True, blank=True)
    techFeature_2 = models.CharField(max_length=200, null=True, blank=True)
    techFeature_3 = models.CharField(max_length=200, null=True, blank=True)
    techFeature_4 = models.CharField(max_length=200, null=True, blank=True)
    techFeature_5 = models.CharField(max_length=200, null=True, blank=True)
    store = models.ForeignKey(
        'store.Store',                 # Link to Store model
        on_delete=models.CASCADE,      # If store is deleted, delete its products
        related_name="rn_products",    # Access with store.products
        null=True, # remove later      # A product can exist without a store
    )
    category = models.ManyToManyField(
        'Category',
        related_name='rn_category_products',
        blank=True  # A product can exist without a category
    )

    def reduce_stock(self, qty: int):
        """
        Atomically reduce stock and log the before/after values.
        Safe for concurrent updates.
        """
        if qty <= 0:
            print(f"[{self.name}] Invalid quantity ({qty}). Skipping update.")
            return

        # Capture the current (initial) quantity from the instance
        initial_qty = self.numberOfItemsAvailable

        # Perform atomic update directly in the DB
        updated = Product.objects.filter(
            id=self.id,
            numberOfItemsAvailable__gte=qty
        ).update(numberOfItemsAvailable=F('numberOfItemsAvailable') - qty)

        if updated:
            # Refresh from database to get the new updated value
            self.refresh_from_db(fields=['numberOfItemsAvailable'])
            print(f"[{self.name}] Stock reduced: {initial_qty} → {self.numberOfItemsAvailable} (-{qty})")

            # Invalidate cache
            clear_key_and_list_in_cache(key='product')
            clear_key_and_list_in_cache(key='store_products')
            clear_key_and_list_in_cache(key='query_category')
        else:
            print(f"[{self.name}] Not enough stock. Available: {initial_qty}, Requested: {qty}. No change made.")

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="rn_subcategories",
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name
