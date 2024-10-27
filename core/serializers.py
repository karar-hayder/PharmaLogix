from rest_framework import serializers

from rest_framework import serializers
from .models import Medication, Cosmetic, Product, PharmacyProduct, Sale, SaleItem

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
    product = ProductSerializer()  # Nesting the ProductSerializer to include full product details

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
# class ProductSerializer(serializers.ModelSerializer):
#     medication_name = serializers.CharField(source='medication.name', read_only=True)
#     generic_name = serializers.CharField(source='medication.generic_name', read_only=True)
#     manufacturer = serializers.CharField(source='medication.manufacturer', read_only=True)
#     barcode = serializers.CharField(source='medication.barcode', read_only=True)
#     ingredients = serializers.CharField(source='medication.active_ingredients', read_only=True)
#     strength = serializers.CharField(source='medication.strength', read_only=True)
#     dosage_form = serializers.CharField(source='medication.dosage_form', read_only=True)

#     class Meta:
#         model = Product
#         fields = ['id', 'medication_name', 'generic_name','manufacturer', 'ingredients','price', 'barcode', 'stock_level','strength','dosage_form','expiration_date']
class SaleItemSerializer(serializers.ModelSerializer):
    product = PharmacyProductSerializer()  # Updated to use PharmacyProductSerializer

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