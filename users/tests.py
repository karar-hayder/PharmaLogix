from django.test import TestCase
from django.contrib.auth.models import User
from .models import Supplier, Pharmacy

class SupplierModelTest(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(name="Test Supplier", contact_info="1234 Test St.")

    def test_supplier_creation(self):
        self.assertIsInstance(self.supplier, Supplier)
        self.assertEqual(self.supplier.name, "Test Supplier")
        self.assertEqual(self.supplier.contact_info, "1234 Test St.")

    def test_supplier_string_representation(self):
        self.assertEqual(str(self.supplier), "Test Supplier")


class PharmacyModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.pharmacy = Pharmacy.objects.create(name="Test Pharmacy", owner=self.user)

    def test_pharmacy_creation(self):
        self.assertIsInstance(self.pharmacy, Pharmacy)
        self.assertEqual(self.pharmacy.name, "Test Pharmacy")
        self.assertEqual(self.pharmacy.owner, self.user)

    def test_pharmacy_string_representation(self):
        self.assertEqual(str(self.pharmacy), "Test Pharmacy")

    def test_pharmacy_workers(self):
        worker1 = User.objects.create_user(username='worker1', password='password123')
        worker2 = User.objects.create_user(username='worker2', password='password123')

        self.pharmacy.workers.add(worker1)
        self.pharmacy.workers.add(worker2)

        self.assertIn(worker1, self.pharmacy.workers.all())
        self.assertIn(worker2, self.pharmacy.workers.all())
        self.assertEqual(self.pharmacy.workers.count(), 2)

