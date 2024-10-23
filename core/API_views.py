from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework.permissions import IsAuthenticated,IsAdminUser,AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Medication, Cosmetic, Pharmacy, Product, PharmacyProduct, Sale, SaleItem
from .serializers import MedicationSerializer, CosmeticSerializer, ProductSerializer, PharmacyProductSerializer, SaleSerializer


class MedicationViewSet(viewsets.ModelViewSet):
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            medication = serializer.save()
            return Response(MedicationSerializer(medication).data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        medication = self.get_object()
        serializer = self.get_serializer(medication, data=request.data, partial=partial)
        if serializer.is_valid():
            medication = serializer.save()
            return Response(MedicationSerializer(medication).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        medication = self.get_object()
        medication.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CosmeticViewSet(viewsets.ModelViewSet):
    queryset = Cosmetic.objects.all()
    serializer_class = CosmeticSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            cosmetic = serializer.save()
            return Response(CosmeticSerializer(cosmetic).data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        cosmetic = self.get_object()
        serializer = self.get_serializer(cosmetic, data=request.data, partial=partial)
        if serializer.is_valid():
            cosmetic = serializer.save()
            return Response(CosmeticSerializer(cosmetic).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        cosmetic = self.get_object()
        cosmetic.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save()
            return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        product = self.get_object()
        serializer = self.get_serializer(product, data=request.data, partial=partial)
        if serializer.is_valid():
            product = serializer.save()
            return Response(ProductSerializer(product).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        product = self.get_object()
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PharmacyProductViewSet(viewsets.ModelViewSet):
    queryset = PharmacyProduct.objects.all()
    serializer_class = PharmacyProductSerializer

    def get_object(self):
        obj = super().get_object()
        if not self.request.user.is_superuser and obj.pharmacy in self.request.user.pharmacies:
            raise PermissionDenied()
        return obj

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            pharmacy_product = serializer.save()
            return Response(PharmacyProductSerializer(pharmacy_product).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        pharmacy_product = self.get_object()
        serializer = self.get_serializer(pharmacy_product, data=request.data, partial=partial)
        if serializer.is_valid():
            pharmacy_product = serializer.save()
            return Response(PharmacyProductSerializer(pharmacy_product).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        pharmacy_product = self.get_object()
        pharmacy_product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Updated CartAPIView with pharmacy_id
class CartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pharmacy_id):
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
        cart = request.session.get('cart', {})
        cart_items = []
        for product_id, item in cart.items():
            pharmacy_product = get_object_or_404(PharmacyProduct, product_id=product_id, pharmacy=pharmacy)
            product_serializer = PharmacyProductSerializer(pharmacy_product).data

            cart_items.append({
                'product': product_serializer,
                'quantity': item.get('quantity', 1),
                'total_price': pharmacy_product.price * item.get('quantity', 1)
            })

        total_price = sum(item['total_price'] for item in cart_items)
        return Response({'cart_items': cart_items, 'total_price': total_price})

    # Post request to add product to cart
    def post(self, request, pharmacy_id, product_id):
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
        pharmacy_product = get_object_or_404(PharmacyProduct, product_id=product_id, pharmacy=pharmacy)
        cart = request.session.get('cart', {})

        quantity = int(request.data.get('quantity', 1))
        if str(product_id) in cart:
            quantity += cart[str(product_id)]['quantity']

        if pharmacy_product.stock_level < quantity:
            return Response({'error': f'The product stock level is low: {pharmacy_product.stock_level}', 'cart': cart}, status=status.HTTP_400_BAD_REQUEST)

        cart[str(product_id)] = {'quantity': quantity}
        request.session['cart'] = cart

        return Response({'message': 'Product added to cart', 'cart': cart}, status=status.HTTP_201_CREATED)

    def patch(self, request, pharmacy_id, product_id):
        cart = request.session.get('cart', {})
        change = int(request.data.get('change', 0))

        if str(product_id) not in cart:
            return Response({'error': 'Product not in cart'}, status=status.HTTP_404_NOT_FOUND)

        current_quantity = cart[str(product_id)]['quantity']
        new_quantity = current_quantity + change

        if new_quantity < 1:
            return Response({'error': 'Quantity cannot be less than 1'}, status=status.HTTP_400_BAD_REQUEST)

        pharmacy_product = get_object_or_404(PharmacyProduct, product_id=product_id, pharmacy_id=pharmacy_id)

        if pharmacy_product.stock_level < new_quantity:
            return Response({'error': f'The product stock level is low: {pharmacy_product.stock_level}'}, status=status.HTTP_400_BAD_REQUEST)

        cart[str(product_id)]['quantity'] = new_quantity
        request.session['cart'] = cart

        return Response({'message': 'Quantity updated', 'cart': cart}, status=status.HTTP_200_OK)

    # Remove product from cart (optional)
    def delete(self, request, pharmacy_id, product_id):
        cart = request.session.get('cart', {})
        if str(product_id) in cart:
            del cart[str(product_id)]
            request.session['cart'] = cart
        return Response({'message': 'Product removed from cart'}, status=status.HTTP_204_NO_CONTENT)


class CheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pharmacy_id):
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
        cart = request.session.get('cart', {})
        payment_received = int(request.data.get('payment_received', 0))
        discount = int(request.data.get('discount', 0))

        if not cart:
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        cart_items = []
        total_price = 0

        for product_id, item in cart.items():
            pharmacy_product = get_object_or_404(PharmacyProduct, id=product_id, pharmacy=pharmacy)
            quantity = item.get('quantity', 1)
            total_price += pharmacy_product.price * quantity
            cart_items.append({
                'product': pharmacy_product,
                'quantity': quantity,
                'price': pharmacy_product.price
            })

        total_amount = total_price - discount

        # if payment_received < total_amount and payment_received != 0:
            # return Response({'error': 'Insufficient payment'}, status=status.HTTP_400_BAD_REQUEST)
        payment_received = total_amount
        sale = Sale.objects.create(
            pharmacy=pharmacy,
            pharmacist=request.user,
            total_amount=total_price,
            payment_received=payment_received,
            discount=discount
        )

        for item in cart_items:
            SaleItem.objects.create(
                sale=sale,
                product=item['product'],
                quantity=item['quantity'],
                price=item['price']
            )
            item['product'].stock_level -= item['quantity']
            item['product'].save()

        request.session['cart'] = {}

        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)

class PharmacyProductSearchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pharmacy_id):
        query = request.GET.get('q', None)
        barcode = request.GET.get('barcode', None)

        if not query and not barcode:
            return Response({'error': 'Search query cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pharmacy = Pharmacy.objects.get(id=pharmacy_id)
        except Pharmacy.DoesNotExist:
            return Response({'error': 'Pharmacy not found'}, status=status.HTTP_404_NOT_FOUND)

        products = None

        if barcode and len(barcode.strip()) >= 10:
            barcode = barcode.strip()
            cache_key = f'products_barcode_{barcode}'
            products = cache.get(cache_key, [])

            if not products:
                products = PharmacyProduct.objects.filter(
                    Q(product__barcode__icontains=barcode),
                    pharmacy=pharmacy
                )
                products = PharmacyProductSerializer(products, many=True).data
                cache.set(cache_key, products, timeout=60)
            
            return Response(products, status=status.HTTP_200_OK if products else status.HTTP_204_NO_CONTENT)

        if query:
            normalized_query = query.strip().lower()
            products = PharmacyProduct.objects.filter(
                Q(product__name__icontains=normalized_query) |
                Q(product__medication__generic_name__icontains=normalized_query) |
                Q(product__barcode__icontains=normalized_query),
                pharmacy=pharmacy
            )
        
        serializer = PharmacyProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK if products else status.HTTP_204_NO_CONTENT)
