from rest_framework import serializers
from .models import Medication, Product, SaleItem, Sale

class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = ('name', 'generic_name', 'manufacturer', 'dosage_form', 'strength', 'active_ingredients', 'rxnorm_code')
        depth = 1

class ProductSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source='medication.name')
    generic_name = serializers.CharField(source='medication.generic_name')
    manufacturer = serializers.CharField(source='medication.manufacturer')

    class Meta:
        model = Product
        fields = ['id', 'medication_name', 'generic_name','manufacturer', 'price', 'barcode', 'stock_level']

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