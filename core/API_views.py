from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework.permissions import IsAuthenticated,IsAdminUser,AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Medication, Product, Sale, SaleItem, Pharmacy
from .serializers import MedicationSerializer,  ProductSerializer, SaleSerializer

class MedicationCreateView(APIView):
    serializer_class = MedicationSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            medication = serializer.save()
            return Response(MedicationSerializer(medication).data)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
# Updated CartAPIView with pharmacy_id
class CartAPIView(APIView):
    def get(self, request, pharmacy_id):
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
        cart = request.session.get('cart', {})
        cart_items = []

        for product_id, item in cart.items():
            product = get_object_or_404(Product, id=product_id, pharmacy=pharmacy)
            cart_items.append({
                'product': ProductSerializer(product).data,
                'quantity': item.get('quantity', 1),
                'total_price': product.price * item.get('quantity', 1)
            })

        total_price = sum(item['total_price'] for item in cart_items)
        return Response({'cart_items': cart_items, 'total_price': total_price})

    # Post request to add product to cart
    def post(self, request, pharmacy_id, product_id):
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
        product = get_object_or_404(Product, id=product_id, pharmacy=pharmacy)
        cart = request.session.get('cart', {})

        # Get the quantity from the request data, defaulting to 1 if not provided
        quantity = int(request.data.get('quantity', 1))

        if str(product_id) not in cart:
            cart[str(product_id)] = {'quantity': quantity}
        else:
            cart[str(product_id)]['quantity'] += quantity

        request.session['cart'] = cart
        return Response({'message': 'Product added to cart', 'cart': cart}, status=status.HTTP_201_CREATED)

    # Remove product from cart (optional)
    def delete(self, request, pharmacy_id, product_id):
        cart = request.session.get('cart', {})
        if str(product_id) in cart:
            del cart[str(product_id)]
            request.session['cart'] = cart
        return Response({'message': 'Product removed from cart'}, status=status.HTTP_204_NO_CONTENT)


# Updated CheckoutAPIView with pharmacy_id
class CheckoutAPIView(APIView):
    def post(self, request, pharmacy_id):
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
        cart = request.session.get('cart', {})
        payment_received = int(request.data.get('payment_received'))
        discount = int(request.data.get('discount'))

        if not cart:
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        cart_items = []
        total_price = 0

        for product_id, item in cart.items():
            product = get_object_or_404(Product, id=product_id, pharmacy=pharmacy)
            quantity = item.get('quantity', 1)
            total_price += product.price * quantity
            cart_items.append({'product': product, 'quantity': quantity, 'price': product.price})

        total_price -= discount
        if payment_received == 0:
            payment_received = total_price

        if payment_received < total_price:
            return Response({'error': 'Insufficient payment'}, status=status.HTTP_400_BAD_REQUEST)

        # Save Sale
        sale = Sale.objects.create(
            pharmacy=pharmacy,
            cashier=request.user,
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

        # Clear cart
        request.session['cart'] = {}

        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)

class ProductSearchAPIView(APIView):
    def get(self, request, pharmacy_id):
        # Get the search query from the request parameters
        query = request.GET.get('q', '').strip()

        # Ensure pharmacy exists
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)

        if not query:
            return Response({'error': 'Search query cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)

        # Search products in the specified pharmacy by medication name, generic name, etc.
        products = Product.objects.filter(
            Q(medication__name__icontains=query) |
            Q(medication__generic_name__icontains=query) |
            Q(medication__manufacturer__icontains=query) |
            Q(medication__dosage_form__icontains=query),
            pharmacy=pharmacy
        )

        # Serialize the results
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)