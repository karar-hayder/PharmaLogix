from django.db import models
from users.models import Pharmacy, Supplier, User
from django.core.exceptions import ValidationError
from django.utils import timezone
# Create your models here.

DOSAGE_FORMS = [
    ('tablet', 'Tablet'),
    ('chewable tablet', 'Chewable Tablet'),
    ('capsule', 'Capsule'),
    ('syrup', 'Syrup'),
    ('injection', 'Injection'),
    ('solution', 'Solution'),
    ('liquid', 'Liquid'),
    ('suspension', 'Suspension'),
    ('elixir', 'Elixir'),
    ('tonic', 'Tonic'),
    ('linctus', 'Linctus'),
    ('pasty', 'Pasty'),
    ('powder', 'Powder'),
    ('granules', 'Granules'),
    ('ointment', 'Ointment'),
    ('cream', 'Cream'),
    ('patch', 'Patch'),
    ('enema', 'Enema'),
    ('gel', 'Gel'),
    ('liniment', 'Liniment'),
    ('suppository', 'Suppository'),
    ('transdermal patch', 'Transdermal Patch'),
    ('nasal spray', 'Nasal Spray'),
    ('topical solution', 'Topical Solution'),
    ('eye drops', 'Eye Drops')
]


class Medication(models.Model):
    name = models.CharField(max_length=255)
    generic_name = models.CharField(max_length=255, blank=True, null=True)
    manufacturer = models.CharField(max_length=255)
    dosage_form = models.CharField(max_length=50, choices=DOSAGE_FORMS)
    strength = models.CharField(max_length=100) 
    active_ingredients = models.TextField(blank=True, null=True)
    rxnorm_code = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name
    class Meta:
        unique_together = ('name','manufacturer','dosage_form','strength')
    
class Product(models.Model):
    pharmacy = models.ForeignKey(Pharmacy,on_delete=models.CASCADE)
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    barcode = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    expiration_date = models.DateField()
    stock_level = models.PositiveIntegerField()
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.medication.name} - {self.price} ({self.stock_level})"
    
    def clean(self):
        if self.expiration_date < timezone.now().date():
            raise ValidationError('Expiration date cannot be in the past.')
    class Meta:
        indexes = [
            models.Index(fields=['barcode']),
        ]

class Sale(models.Model):
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE)
    cashier = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.PositiveIntegerField()
    discount = models.PositiveIntegerField()
    

    def __str__(self):
        return f"Sale #{self.id} - {self.total_amount} by {self.cashier.username} at {self.created_at.strftime('%d/%m/%Y, %H:%M:%S')}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.PositiveIntegerField()

    def total_price(self):
        return self.quantity * self.price