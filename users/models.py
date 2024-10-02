from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_info = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Pharmacy(models.Model):
    name = models.CharField('Name',max_length=255)
    owner = models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
    workers = models.ManyToManyField(User,related_name='pharmacies')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Pharmacy"
        verbose_name_plural = "Pharmacies"