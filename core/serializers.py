from rest_framework import serializers

from rest_framework import serializers
from .models import Medication, Cosmetic, Product, PharmacyProduct, Sale, SaleItem
from users.serializers import SupplierSerializer
class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = '__all__'

class CosmeticSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cosmetic
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    medication = MedicationSerializer(read_only=True)
    cosmetic = CosmeticSerializer(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'product_type', 'barcode', 'medication', 'cosmetic']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if isinstance(instance, Medication):
            representation['type'] = "Medication"
        elif isinstance(instance, Cosmetic):
            representation['type'] = "Cosmetic"
        return representation


class PharmacyProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    supplier = SupplierSerializer(read_only=True)
    class Meta:
        model = PharmacyProduct
        fields = ['id', 'product', 'pharmacy_id', 'supplier_price', 'price', 'expiration_date', 'stock_level', 'supplier']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        product = instance.product
        representation['product_name'] = product.name
        representation['product_type'] = product.product_type

        if isinstance(product, Medication):
            representation['medication'] = {
                'generic_name': product.generic_name,
                'manufacturer': product.manufacturer,
                'dosage_form': product.dosage_form,
                'strength': product.strength,
                'active_ingredients': product.active_ingredients,
            }
        elif isinstance(product, Cosmetic):
            representation['cosmetic'] = {
                'brand': product.brand,
                'type': product.type,
                'ingredients': product.ingredients,
            }

        return representation
    def update(self, instance, validated_data):
        # Update the PharmacyProduct instance
        instance.supplier_price = validated_data.get('supplier_price', instance.supplier_price)
        instance.price = validated_data.get('price', instance.price)
        instance.expiration_date = validated_data.get('expiration_date', instance.expiration_date)
        instance.stock_level = validated_data.get('stock_level', instance.stock_level)
        instance.save()

        return instance
    

class SaleItemSerializer(serializers.ModelSerializer):
    product = PharmacyProductSerializer()

    class Meta:
        model = SaleItem
        fields = ['id', 'product', 'quantity', 'price']

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price must be a positive value.")
        return value


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True)

    class Meta:
        model = Sale
        fields = ['id', 'total_amount', 'payment_received', 'items', 'discount']

    @property
    def final_amount(self):
        return self.total_amount - self.discount

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        sale = Sale.objects.create(**validated_data)
        for item_data in items_data:
            product_data = item_data.pop('product')
            product = PharmacyProduct.objects.get(id=product_data['id'])
            SaleItem.objects.create(sale=sale, product=product, **item_data)
        return sale

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        instance.total_amount = validated_data.get('total_amount', instance.total_amount)
        instance.payment_received = validated_data.get('payment_received', instance.payment_received)
        instance.discount = validated_data.get('discount', instance.discount)
        instance.save()

        if items_data:
            instance.items.all().delete()
            for item_data in items_data:
                product_data = item_data.pop('product')
                product = PharmacyProduct.objects.get(id=product_data['id'])
                SaleItem.objects.create(sale=instance, product=product, **item_data)

        return instance