from django.db import models

# Create your models here.
class ProductAdvert(models.Model):
    anchor = models.CharField(max_length=200)
    paragraph = models.TextField()
    discount = models.CharField(max_length=200)
    image_url = models.URLField(blank=True, null=True)  # only store ImageKit URL
    fileId = models.CharField(max_length=200, null=True, blank=True)  # store ImageKit fileId

    def __str__(self):
        return self.discount
