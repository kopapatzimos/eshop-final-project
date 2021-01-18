from django.db import models

# Create your models here.
from django.db import models
import numpy as np
from core.models import Item
from taggit.managers import TaggableManager


class Review(models.Model):
    RATING_CHOICES = (
        (1, "1"),
        (2, "2"),
        (3, "3"),
        (4, "4"),
        (5, "5"),
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    pub_date = models.DateTimeField("date published")
    user_name = models.CharField(max_length=100)
    comment = models.CharField(max_length=200)
    rating = models.IntegerField(choices=RATING_CHOICES)
    tags = TaggableManager()
