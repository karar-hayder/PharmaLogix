from django.db import models
from users.models import Pharmacy, Supplier, User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone
from django.db.models import UniqueConstraint
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


class Product(models.Model):
    name = models.CharField(max_length=255)
    product_type = models.CharField(max_length=50)
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True, validators=[
        RegexValidator(regex='^\\d+$', message='Barcode must be numeric.')
    ])


    
    def __str__(self):
        return self.name

class Medication(Product):
    generic_name = models.CharField(max_length=255, blank=True, null=True)
    manufacturer = models.CharField(max_length=255)
    dosage_form = models.CharField(max_length=50, choices=DOSAGE_FORMS)
    strength = models.CharField(max_length=100)
    active_ingredients = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} [{self.generic_name}] - {self.dosage_form} - {self.strength}"

    class Meta:
        unique_together = ('generic_name', 'manufacturer', 'dosage_form', 'strength')
    
class Cosmetic(Product):
    brand = models.CharField(max_length=200)
    type = models.CharField(max_length=100)
    ingredients = models.TextField(blank=True)

class PharmacyProduct(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE)
    price = models.PositiveBigIntegerField()
    expiration_date = models.DateField()
    stock_level = models.PositiveIntegerField()
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('product', 'pharmacy', 'supplier')

    def __str__(self):
        return f"{self.product.name} at {self.pharmacy.name} from {self.supplier.name} - {self.price} IQD ({self.stock_level})"

    def clean(self):
        if self.expiration_date and self.expiration_date < timezone.now().date():
            raise ValidationError('Expiration date cannot be in the past.')

class Sale(models.Model):
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE,related_name='sales')
    pharmacist = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.PositiveIntegerField()
    discount = models.PositiveIntegerField()
    payment_received  = models.PositiveIntegerField()

    def __str__(self):
        return f"Sale #{self.id} - {self.total_amount} by {self.pharmacist.username} at {self.created_at.strftime('%d/%m/%Y, %H:%M:%S')}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(PharmacyProduct, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.PositiveIntegerField()

    @property
    def total_price(self):
        return self.quantity * self.price