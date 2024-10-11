from rest_framework import serializers
from .models import Medication, Product, SaleItem, Sale

class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = ('pk','name', 'generic_name', 'manufacturer', 'dosage_form', 'strength', 'active_ingredients', 'barcode','rxnorm_code')
        depth = 1

class ProductSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source='medication.name', read_only=True)
    generic_name = serializers.CharField(source='medication.generic_name', read_only=True)
    manufacturer = serializers.CharField(source='medication.manufacturer', read_only=True)
    barcode = serializers.CharField(source='medication.barcode', read_only=True)
    ingredients = serializers.CharField(source='medication.active_ingredients', read_only=True)
    strength = serializers.CharField(source='medication.strength', read_only=True)
    dosage_form = serializers.CharField(source='medication.dosage_form', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'medication_name', 'generic_name','manufacturer', 'ingredients','price', 'barcode', 'stock_level','strength','dosage_form','expiration_date']

class SaleItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = SaleItem
        fields = ['id', 'product', 'quantity', 'price']

class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True)

    class Meta:
        model = Sale
        fields = ['id', 'total_amount', 'payment_received', 'items']