from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.cache import cache
# Create your models here.



class Pharmacy(models.Model):
    name = models.CharField('Name',max_length=255)
    owner = models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
    workers = models.ManyToManyField(User,related_name='pharmacies')
    address = models.TextField(null=True,blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    def __str__(self):
        return self.name
    
    @property
    def subscription(self):
        sub : Subscription = cache.get(f'{self.pk}-sub')
        if not sub:
            sub = self.subscriptions.last()
            cache.set(f"{self.pk}-sub",sub,60*60)
        return sub
    def has_feature(self, feature_name: str) -> bool:
        """Check if the pharmacy's current subscription includes the specified feature."""
        cache_key = f"{self.pk}-has_feature-{feature_name}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        subscription = self.subscription
        has_feature = subscription and subscription.plan.features.filter(tag=feature_name).exists()
        cache.set(cache_key, has_feature, timeout=60 * 60)
        return has_feature
        
    class Meta:
        verbose_name = "Pharmacy"
        verbose_name_plural = "Pharmacies"

class Supplier(models.Model):
    pharmacy = models.ForeignKey(Pharmacy,on_delete=models.SET_NULL,null=True,related_name='suppliers')
    office = models.CharField('Office or dispensary',max_length=255,blank=True)
    contact_info = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.office
class SubscriptionFeature(models.Model):
    name = models.CharField(max_length=255)
    tag = models.CharField(max_length=255)
    level = models.PositiveIntegerField(default=0)
    description = models.TextField()

    def __str__(self):
        return self.name
    
class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    duration_days = models.PositiveIntegerField('Subscription Duration (days)', default=30)
    price = models.PositiveIntegerField()
    discount_percentage = models.PositiveIntegerField('Discount Percentage', default=0)
    features = models.ManyToManyField(SubscriptionFeature, related_name='plans',blank=True)
    description = models.TextField(blank=True, null=True)
    featured = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.duration_days} days - {self.total_price} IQD (discount {self.discount_percentage}% * {self.price})"
    
    def clean(self):
        if not (0 <= self.discount_percentage <= 100):
            raise ValidationError('Discount percentage must be between 0 and 100.')
    @property
    def total_price(self):
        discount_amount = (self.price * self.discount_percentage / 100)
        discounted_price = self.price - discount_amount
        normalized_price = ((discounted_price + 125) // 250) * 250
        return int(normalized_price)
    
class Subscription(models.Model):
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateField(default=timezone.now)
    extended = models.PositiveIntegerField(null=True,blank=True)
    end_date = models.DateField(blank=True, null=True)
    paid = models.PositiveIntegerField(null=True,blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.end_date = self.start_date + timedelta(days=self.plan.duration_days + (self.extended or 0))
        if not self.paid:
            self.paid = self.plan.total_price
        super(Subscription, self).save(*args, **kwargs)
    
    @property
    def is_active(self):
        return self.end_date >= timezone.now().date()

    def __str__(self):
        status = "Active" if self.is_active else "Expired"
        return f"{self.pharmacy.name} - {self.plan.name} (From: {self.start_date} to {self.end_date}) - Status: {status}"
