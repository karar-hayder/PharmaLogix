from django.test import TestCase
from django.contrib.auth.models import User
from .models import Supplier, Pharmacy, SubscriptionPlan, SubscriptionFeature, Subscription

class SupplierModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.pharmacy = Pharmacy.objects.create(name="Test Pharmacy", owner=self.user)
        self.supplier = Supplier.objects.create(pharmacy=self.pharmacy, office="Test Office", contact_info="1234 Test St.")

    def test_supplier_creation(self):
        self.assertIsInstance(self.supplier, Supplier)
        self.assertEqual(self.supplier.office, "Test Office")
        self.assertEqual(self.supplier.contact_info, "1234 Test St.")
        self.assertEqual(self.supplier.pharmacy, self.pharmacy)

    def test_supplier_string_representation(self):
        self.assertEqual(str(self.supplier), "Test Office")


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

    def test_subscription_feature_check(self):
        feature = SubscriptionFeature.objects.create(name="Basic Inventory", tag="basic_inventory_audit", description="Basic inventory audit feature.")
        plan = SubscriptionPlan.objects.create(name="Basic Plan", duration_days=30, price=1000, discount_percentage=0)
        plan.features.add(feature)

        subscription = Subscription.objects.create(pharmacy=self.pharmacy, plan=plan)

        self.assertTrue(self.pharmacy.has_feature("basic_inventory_audit"))
        self.assertFalse(self.pharmacy.has_feature("non_existent_feature"))

    def test_subscription_creation(self):
        plan = SubscriptionPlan.objects.create(name="Monthly Plan", duration_days=30, price=1200, discount_percentage=10)
        subscription = Subscription.objects.create(pharmacy=self.pharmacy, plan=plan)

        self.assertEqual(subscription.pharmacy, self.pharmacy)
        self.assertEqual(subscription.plan, plan)
        self.assertIsNotNone(subscription.start_date)
        self.assertIsNotNone(subscription.end_date)

    def test_subscription_total_price(self):
        plan = SubscriptionPlan.objects.create(name="Premium Plan", duration_days=30, price=12000, discount_percentage=15)
        self.assertEqual(plan.total_price, 10250)
