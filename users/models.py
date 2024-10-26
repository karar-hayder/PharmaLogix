from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone
from django.db.models import UniqueConstraint
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
    features = models.ManyToManyField(SubscriptionFeature, related_name='plans')
    description = models.TextField(blank=True, null=True)
    featured = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.duration_days} days - X{self.price}X {self.total_price} IQD (discount {self.discount_percentage}%)"
    
    def clean(self):
        if not (0 <= self.discount_percentage <= 100):
            raise ValidationError('Discount percentage must be between 0 and 100.')
    @property
    def total_price(self):
        discount_amount = (self.price * self.discount_percentage / 100)
        discount_amount_overflow =  discount_amount % 250
        if discount_amount_overflow < 125:
            normalized_discount_amount = discount_amount - discount_amount_overflow
        else:
            normalized_discount_amount = discount_amount + discount_amount_overflow
        return int(self.price - normalized_discount_amount)
    
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
