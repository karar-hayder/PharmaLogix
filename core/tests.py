from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import Medication, Product, Sale, SaleItem
from users.models import Pharmacy, Supplier, User
from django.utils import timezone


class MedicationModelTest(TestCase):

    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(name='Test Pharmacy', owner=User.objects.create(username='owner'))
        self.supplier = Supplier.objects.create(name='Test Supplier', contact_info='123-456-7890')
        self.medication = Medication.objects.create(
            name='Aspirin',
            generic_name='Acetylsalicylic Acid',
            manufacturer='Test Manufacturer',
            dosage_form='tablet',
            strength='500mg',
            active_ingredients='Acetylsalicylic Acid',
            barcode='123456789012'
        )

    def test_medication_creation(self):
        self.assertEqual(self.medication.name, 'Aspirin')
        self.assertEqual(self.medication.strength, '500mg')

    def test_medication_str(self):
        self.assertEqual(str(self.medication), 'Aspirin')


class ProductModelTest(TestCase):

    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(name='Test Pharmacy', owner=User.objects.create(username='owner'))
        self.supplier = Supplier.objects.create(name='Test Supplier', contact_info='123-456-7890')
        self.medication = Medication.objects.create(
            name='Aspirin',
            manufacturer='Test Manufacturer',
            dosage_form='tablet',
            strength='500mg',
            active_ingredients='Acetylsalicylic Acid',
            barcode='123456789012'
        )
        self.product = Product.objects.create(
            pharmacy=self.pharmacy,
            medication=self.medication,
            price=1000,
            expiration_date=timezone.now() + timezone.timedelta(days=30),
            stock_level=50,
            supplier=self.supplier
        )

    def test_product_creation(self):
        self.assertEqual(self.product.pharmacy, self.pharmacy)
        self.assertEqual(self.product.price, 1000)
        self.assertTrue(self.product.expiration_date > timezone.now())
        self.assertEqual(self.product.supplier, self.supplier)

    def test_product_expiration_date_validation(self):
        product = Product(
            pharmacy=self.pharmacy,
            medication=self.medication,
            price=1000,
            expiration_date=timezone.now() - timezone.timedelta(days=1),
            stock_level=50
        )
        with self.assertRaises(ValidationError):
            product.clean()

    def test_product_str(self):
        self.assertEqual(str(self.product), 'Aspirin - 1000 (50)')


class SaleModelTest(TestCase):

    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(name='Test Pharmacy', owner=User.objects.create(username='owner'))
        self.user = User.objects.create(username='cashier', password='password')
        self.sale = Sale.objects.create(
            pharmacy=self.pharmacy,
            cashier=self.user,
            total_amount=10000,
            discount=1000,
            payment_received=9000
        )

    def test_sale_creation(self):
        self.assertEqual(self.sale.total_amount, 10000)
        self.assertEqual(self.sale.discount, 1000)

    def test_sale_str(self):
        self.assertEqual(str(self.sale), f'Sale #{self.sale.id} - 10000 by {self.user.username} at {self.sale.created_at.strftime("%d/%m/%Y, %H:%M:%S")}')


class SaleItemModelTest(TestCase):

    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(name='Test Pharmacy', owner=User.objects.create(username='owner'))
        self.supplier = Supplier.objects.create(name='Test Supplier', contact_info='123-456-7890')
        self.medication = Medication.objects.create(
            name='Aspirin',
            manufacturer='Test Manufacturer',
            dosage_form='tablet',
            strength='500mg',
            active_ingredients='Acetylsalicylic Acid',
            barcode='123456789012'
        )
        self.product = Product.objects.create(
            pharmacy=self.pharmacy,
            medication=self.medication,
            price=1000,
            expiration_date=timezone.now() + timezone.timedelta(days=30),
            stock_level=50,
            supplier=self.supplier
        )
        self.sale = Sale.objects.create(
            pharmacy=self.pharmacy,
            cashier=User.objects.create(username='cashier', password='password'),
            total_amount=10000,
            discount=1000,
            payment_received=9000
        )
        self.sale_item = SaleItem.objects.create(
            sale=self.sale,
            product=self.product,
            quantity=2,
            price=1000
        )

    def test_sale_item_creation(self):
        self.assertEqual(self.sale_item.quantity, 2)
        self.assertEqual(self.sale_item.price, 1000)

    def test_sale_item_total_price(self):
        self.assertEqual(self.sale_item.total_price(), 2000)

