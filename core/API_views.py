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

from .models import Medication, Product, Sale, SaleItem, Pharmacy
from .serializers import MedicationSerializer,  ProductSerializer, SaleSerializer

class MedicationCreateView(APIView):
    serializer_class = MedicationSerializer
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            medication = serializer.save()
            return Response(MedicationSerializer(medication).data)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
class MedicationSearchView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        name = request.query_params.get('name', None)
        pk = request.query_params.get('pk', None)
        barcode = request.query_params.get('barcode', None)
        if not name and not pk and not barcode:
            return Response({"error": "No search term provided."}, status=status.HTTP_400_BAD_REQUEST)

        query = Q()
        if pk != None:
            query |= Q(pk=pk)
        if barcode != None:
            query |= Q(barcode=str(barcode))
        if name != None:
            query |= Q(name__icontains=name) | Q(generic_name__icontains=name)
        medications = Medication.objects.filter(query)
        if medications.exists():
            serializer = MedicationSerializer(medications, many=True)
            return Response(serializer.data, status=200)
        else:
            return Response([], status=200)
        
# Updated CartAPIView with pharmacy_id
class CartAPIView(APIView):
    permission_classes = [IsAuthenticated]
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
        if str(product_id) in cart:
            quantity += cart[str(product_id)]['quantity']
        if product.stock_level < quantity:
            return Response({'error': f'The product stock level is low: {product.stock_level}', 'cart': cart}, status=status.HTTP_400_BAD_REQUEST)    
        
        cart[str(product_id)] = {'quantity': quantity}
        

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
    permission_classes = [IsAuthenticated]
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

        payment_received = total_price - discount

        # if payment_received < total_price:
        #     return Response({'error': 'Insufficient payment'}, status=status.HTTP_400_BAD_REQUEST)

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
    permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]
    def get(self, request, pharmacy_id):
        # Get the search query from the request parameters
        query = request.GET.get('q', None)
        barcode = request.GET.get('barcode',None)

        # Ensure pharmacy exists
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
        products = None
        if not query and not barcode:
            return Response({'error': 'Search query cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)
        if barcode and len(barcode.strip())>=10:
            barcode = barcode.strip()
            cache_key = f'products_barcode_{barcode}'
            products = cache.get(cache_key)

            if products is None:
                products = Product.get_products_by_barcode(pharmacy, barcode)
                products = ProductSerializer(products, many=True).data
                cache.set(cache_key, products, timeout=60)
            return Response(products, status=status.HTTP_200_OK if products else status.HTTP_204_NO_CONTENT)
            
            
        if query:
            query = query.strip()
            products = Product.objects.filter(
                Q(medication__name__icontains=query) |
                Q(medication__generic_name__icontains=query) |
                Q(medication__manufacturer__icontains=query) |
                Q(medication__barcode__icontains=query) |
                Q(medication__dosage_form__icontains=query),
                pharmacy=pharmacy
            )
        
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK if products else status.HTTP_204_NO_CONTENT)
class ProductUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pharmacy_id,product_id):
        quantity = request.data.get('quantity')
        expiration_date_str = request.data.get('expiration_date')

        if not product_id or not quantity or not expiration_date_str:
            return Response({'error': 'Product ID, quantity, and expiration date are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = get_object_or_404(Product, id=int(product_id), pharmacy_id=int(pharmacy_id))

            expiration_date = timezone.datetime.strptime(expiration_date_str, '%Y-%m-%d').date()

            if expiration_date < timezone.now().date():
                return Response({'error': 'Expiration date cannot be in the past.'}, status=status.HTTP_400_BAD_REQUEST)

            product.stock_level += int(quantity)
            product.expiration_date = expiration_date
            product.save()

            return Response({'success': 'Product updated successfully.'}, status=status.HTTP_200_OK)
        
        except ValidationError as e:
            
            return Response({'error': f"{e.messages}"}, status=status.HTTP_400_BAD_REQUEST)
        
        except Product.DoesNotExist:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        

class ProductCreateView(APIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, pharmacy_id,med_id):
        serializer = self.serializer_class(data=request.data)
        pharmacy = get_object_or_404(Pharmacy,id=pharmacy_id)
        med = get_object_or_404(Medication,id=med_id)
        if serializer.is_valid():
            product = serializer.save(pharmacy=pharmacy,medication=med)
            return Response(ProductSerializer(product).data)
        print(serializer.errors)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
