from django.db import models

# Create your models here.
class Carousel(models.Model):
    heading = models.CharField(max_length=200)
    paragraph = models.TextField()
    anchor = models.CharField(max_length=200, blank=True, null=True)  # Optional anchor link
    image_url = models.URLField(blank=True, null=True)  # only store ImageKit URL
    fileId = models.CharField(max_length=200, null=True, blank=True)  # store ImageKit fileId

    def __str__(self):
        return self.heading
