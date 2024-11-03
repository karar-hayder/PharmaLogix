from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from .models import Medication, Cosmetic, Product, PharmacyProduct, Sale, SaleItem
from users.models import Pharmacy, Supplier, User

### Product Tests
class ProductModelTest(TestCase):

    def test_create_product(self):
        product = Product.objects.create(
            name="Test Product", 
            product_type="medication", 
            barcode="123456789012"
        )
        self.assertEqual(str(product), "Test Product")

    def test_create_medication(self):
        medication = Medication.objects.create(
            name="Test Medication", 
            generic_name="Generic", 
            manufacturer="Test Manufacturer", 
            dosage_form="tablet", 
            strength="500mg",
            active_ingredients="Ingredient 1, Ingredient 2"
        )
        self.assertEqual(str(medication), "Test Medication [Generic] - tablet - 500mg")

    def test_create_cosmetic(self):
        cosmetic = Cosmetic.objects.create(
            name="Test Cosmetic", 
            brand="Test Brand", 
            type="Face Cream", 
            ingredients="Ingredient 1, Ingredient 2"
        )
        self.assertEqual(str(cosmetic), "Test Cosmetic")

    def test_medication_unique_constraint(self):
        Medication.objects.create(
            name="Test Medication", 
            generic_name="Generic", 
            manufacturer="Test Manufacturer", 
            dosage_form="tablet", 
            strength="500mg"
        )
        with self.assertRaises(ValidationError):
            medication = Medication(
                name="Test Medication", 
                generic_name="Generic", 
                manufacturer="Test Manufacturer", 
                dosage_form="tablet", 
                strength="500mg"
            )
            medication.full_clean()

### PharmacyProduct Tests
class PharmacyProductModelTest(TestCase):

    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(name="Test Pharmacy", owner=User.objects.create(username="owner"))
        self.medication = Medication.objects.create(
            name="Test Medication", 
            generic_name="Generic", 
            manufacturer="Test Manufacturer", 
            dosage_form="tablet", 
            strength="500mg"
        )
        self.supplier = Supplier.objects.create(pharmacy=self.pharmacy, office="Test Office", contact_info="1234 Test St.")


    def test_create_pharmacy_product(self):
        pharmacy_product = PharmacyProduct.objects.create(
            product=self.medication, 
            pharmacy=self.pharmacy, 
            supplier=self.supplier,
            price=2000000,  # Adjusted to thousands
            supplier_price=1000000,  # Adjusted to thousands
            expiration_date=timezone.now().date() + timedelta(days=30), 
            stock_level=50
        )
        self.assertEqual(str(pharmacy_product), "Test Medication at Test Pharmacy from Test Office - 2000000 IQD (50)")

    def test_expired_product_validation(self):
        expired_date = timezone.now().date() - timedelta(days=1)
        pharmacy_product = PharmacyProduct(
            product=self.medication, 
            pharmacy=self.pharmacy, 
            supplier=self.supplier,
            price=2000000,  # Adjusted to thousands
            supplier_price=1000000,  # Adjusted to thousands
            expiration_date=expired_date, 
            stock_level=50
        )
        with self.assertRaises(ValidationError):
            pharmacy_product.clean()

    def test_unique_constraint(self):
        PharmacyProduct.objects.create(
            product=self.medication, 
            pharmacy=self.pharmacy, 
            supplier=self.supplier,
            price=2000000,  # Adjusted to thousands
            supplier_price=1000000,  # Adjusted to thousands
            expiration_date=timezone.now().date() + timedelta(days=30), 
            stock_level=50
        )
        with self.assertRaises(ValidationError):
            pharmacy_product = PharmacyProduct(
                product=self.medication, 
                pharmacy=self.pharmacy, 
                supplier=self.supplier,
                price=2000000,  # Adjusted to thousands
                supplier_price=1000000,  # Adjusted to thousands
                expiration_date=timezone.now().date() + timedelta(days=60), 
                stock_level=50
            )
            pharmacy_product.full_clean()

### Sale and SaleItem Tests
class SaleModelTest(TestCase):

    def setUp(self):
        self.pharmacy = Pharmacy.objects.create(name="Test Pharmacy", owner=User.objects.create(username="owner"))
        self.user = User.objects.create_user(username="testuser", password="password")
        self.pharmacy_product = PharmacyProduct.objects.create(
            product=Product.objects.create(name="Test Product", product_type="medication"),
            pharmacy=self.pharmacy, 
            price=2000000,  # Adjusted to thousands
            supplier_price=1000000,  # Adjusted to thousands
            expiration_date=timezone.now().date() + timedelta(days=60), 
            stock_level=100
        )

    def test_create_sale(self):
        sale = Sale.objects.create(
            pharmacy=self.pharmacy, 
            pharmacist=self.user, 
            total_amount=500000,  # Adjusted to thousands
            discount=50000,  # Adjusted to thousands
            payment_received=450000  # Adjusted to thousands
        )
        self.assertEqual(str(sale), f"Sale #{sale.id} - 500000 by testuser at {sale.created_at.strftime('%d/%m/%Y, %H:%M:%S')}")

    def test_create_sale_item(self):
        sale = Sale.objects.create(
            pharmacy=self.pharmacy, 
            pharmacist=self.user, 
            total_amount=500000,  # Adjusted to thousands
            discount=50000,  # Adjusted to thousands
            payment_received=450000  # Adjusted to thousands
        )
        sale_item = SaleItem.objects.create(
            sale=sale, 
            product=self.pharmacy_product, 
            quantity=5, 
            price=100000  # Adjusted to thousands
        )
        self.assertEqual(sale_item.total_price, 500000)  # 5 * 100000

    def test_sale_item_quantity(self):
        sale = Sale.objects.create(
            pharmacy=self.pharmacy, 
            pharmacist=self.user, 
            total_amount=500000,  # Adjusted to thousands
            discount=50000,  # Adjusted to thousands
            payment_received=450000  # Adjusted to thousands
        )
        sale_item = SaleItem.objects.create(
            sale=sale, 
            product=self.pharmacy_product, 
            quantity=3, 
            price=100000  # Adjusted to thousands
        )
        self.assertEqual(sale_item.total_price, 300000)  # 3 * 100000
