from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render
from django.views.generic import TemplateView, UpdateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Pharmacy, Medication, Sale, SaleItem, models
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from rest_framework import status
from .serializers import MedicationSerializer
import json
from django.core.cache import cache
# Create your views here.


class IndexView(TemplateView):
    template_name = 'base.html'


class Home(LoginRequiredMixin,TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['pharmacies'] = self.request.user.pharmacies.all()
        return context

class Work(LoginRequiredMixin,UserPassesTestMixin,TemplateView):
    template_name = 'core/work.html'

    def test_func(self) -> bool | None:
        pharmacy_id = self.kwargs.get('pharmacy_id')
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
        return pharmacy in self.request.user.pharmacies.all()
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pharmacy_id = self.kwargs.get('pharmacy_id')
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
        context['pharmacy'] = pharmacy
        return context

class BarcodeAdderView(LoginRequiredMixin,UserPassesTestMixin,TemplateView):
    template_name = 'core/barcode_add.html'

    def test_func(self) -> bool | None:
        return self.request.user.is_superuser
    def post(self, request, *args, **kwargs):
        barcode = request.POST.get('barcode')

        if not barcode:
            return JsonResponse({"error": "Barcode is required"}, status=400)

        try:
            medication = Medication.objects.get(barcode=barcode)
            data = MedicationSerializer(medication).data
            return JsonResponse({
                "message": "Medication found",
                "medication": data
            }, status=200)

        except Medication.DoesNotExist:
            return JsonResponse({
                "message": "Medication not found. Please search or create a new one."
            }, status=404)

    def put(self, request, *args, **kwargs):

        try:
            put_data = json.loads(request.body.decode('utf-8'))
            medication_id = put_data.get('medication_id')
            barcode = put_data.get('barcode')

            if not medication_id or not barcode:
                return JsonResponse({"error": "Medication ID and barcode are required."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                medication = Medication.objects.get(id=medication_id)
            except Medication.DoesNotExist:
                return JsonResponse({"error": "Medication not found."}, status=status.HTTP_404_NOT_FOUND)

            medication.barcode = barcode

            if 'name' in put_data:
                medication.name = put_data['name']
            if 'generic_name' in put_data:
                medication.generic_name = put_data['generic_name']
            if 'manufacturer' in put_data:
                medication.manufacturer = put_data['manufacturer']
            if 'dosage_form' in put_data:
                medication.dosage_form = put_data['dosage_form']
            if 'strength' in put_data:
                medication.strength = put_data['strength']
            if 'active_ingredients' in put_data:
                medication.active_ingredients = put_data['active_ingredients']

            medication.save()
            data = MedicationSerializer(medication).data

            return JsonResponse({
                "message": "Medication successfully updated.",
                "medication": data
            }, status=status.HTTP_200_OK)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=status.HTTP_400_BAD_REQUEST)
        
class AddProductsView(LoginRequiredMixin,UserPassesTestMixin,TemplateView):
    template_name = 'core/med_add.html'
    
    def test_func(self) -> bool | None:
        pharmacy_id = self.kwargs.get('pharmacy_id')
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
        return pharmacy in self.request.user.pharmacies.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pharmacy_id = self.kwargs.get('pharmacy_id')
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
        context['pharmacy'] = pharmacy
        return context
    
class SalesListView(LoginRequiredMixin,UserPassesTestMixin,ListView):
    model = Sale
    template_name = 'core/sale_list.html'
    context_object_name = 'sales'

    def test_func(self) -> bool | None:
        pharmacy_id = self.kwargs.get('pharmacy_id')
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
        return pharmacy in self.request.user.pharmacies.all()
    
    def get_queryset(self):
        pharmacy_id = self.kwargs.get('pharmacy_id')
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
        query = cache.get('sales_metrics')
        query = self.model.objects.filter(pharmacy=pharmacy).order_by('-created_at')
        return query

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        pharmacy_id = self.kwargs.get('pharmacy_id')
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
        metrics = cache.get(f'{pharmacy_id}-sales_metrics')

        if not metrics:
            pharmacy_sales = self.model.objects.filter(pharmacy=pharmacy)
            total_sales_count = pharmacy_sales.count()
            total_sales_amount = pharmacy_sales.aggregate(total=models.Sum('total_amount'))['total'] or 0
            total_discount = pharmacy_sales.aggregate(total=models.Sum('discount'))['total'] or 0
            total_payment_received = pharmacy_sales.aggregate(total=models.Sum('payment_received'))['total'] or 0

            average_sale_amount = round((total_sales_amount / total_sales_count if total_sales_count > 0 else 0),3)

            best_selling_product_item = (
                SaleItem.objects.filter(sale__pharmacy=pharmacy).values('product__medication__name')
                .annotate(total_sales=models.Sum('price'))
                .order_by('-total_sales')
                .first()
            )
            best_selling_product = best_selling_product_item['product__medication__name'] if best_selling_product_item else "None"
            best_selling_product_revenue = best_selling_product_item['total_sales'] if best_selling_product_item else 0

            metrics = {
                'total_sales_count': total_sales_count,
                'total_sales_amount': total_sales_amount,
                'total_discount': total_discount,
                'total_payment_received': total_payment_received,
                'average_sale_amount': average_sale_amount,
                'best_selling_product': best_selling_product,
                'best_selling_product_revenue': best_selling_product_revenue,
            }

            cache.set('sales_metrics', metrics, timeout=60*5)
        context["metrics"] = metrics
        return context
    
    