from django.contrib import admin
from .models import Medication, Product, Sale, SaleItem, Cosmetic, PharmacyProduct
# Register your models here.

admin.site.register(Medication)
admin.site.register(Cosmetic)
admin.site.register(Product)
admin.site.register(PharmacyProduct)
admin.site.register(Sale)
admin.site.register(SaleItem)