from django.db import models

# fulldesc = """Eos no lorem eirmod diam diam, eos elitr et gubergren diam sea. Consetetur vero aliquyam invidunt duo dolores et duo sit. Vero diam ea vero et dolore rebum, dolor rebum eirmod consetetur invidunt sed sed et, lorem duo et eos elitr, sadipscing kasd ipsum rebum diam. Dolore diam stet rebum sed tempor kasd eirmod. Takimata kasd ipsum accusam sadipscing, eos dolores sit no ut diam consetetur duo justo est, sit sanctus diam tempor aliquyam eirmod nonumy rebum dolor accusam, ipsum kasd eos consetetur at sit rebum, diam kasd invidunt tempor lorem, ipsum lorem elitr sanctus eirmod takimata dolor ea invidunt.
# Dolore magna est eirmod sanctus dolor, amet diam et eirmod et ipsum. Amet dolore tempor consetetur sed lorem dolor sit lorem tempor. Gubergren amet amet labore sadipscing clita clita diam clita. Sea amet et sed ipsum lorem elitr et, amet et labore voluptua sit rebum. Ea erat sed et diam takimata sed justo. Magna takimata justo et amet magna et.
# """
# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    fullDescription = models.TextField()
    marketingDescription = models.TextField(null=True, blank=True)
    marketPrice = models.DecimalField(max_digits=10, decimal_places=2)
    discountPrice = models.DecimalField(max_digits=10, decimal_places=2)
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
    
    ##### add a many-to-many relationship to the Category model (a product can belong to many categories and vice versa)

    def __str__(self):
        return self.name
