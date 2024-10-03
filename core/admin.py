from django.contrib import admin
from .models import Medication, Product, Sale, SaleItem
# Register your models here.

admin.site.register(Medication)
admin.site.register(Product)
admin.site.register(Sale)
admin.site.register(SaleItem)