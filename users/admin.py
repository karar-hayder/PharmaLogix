from django.contrib import admin
from .models import Pharmacy, Supplier, SubscriptionFeature, SubscriptionPlan, Subscription
# Register your models here.

admin.site.register(Pharmacy)
admin.site.register(Supplier)
admin.site.register(SubscriptionFeature)
admin.site.register(SubscriptionPlan)
admin.site.register(Subscription)
