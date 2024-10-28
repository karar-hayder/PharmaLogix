from typing import Any
from django.utils import timezone
from datetime import timedelta
from django.db.models.query import QuerySet
from django.shortcuts import render
from django.views.generic import TemplateView, UpdateView, ListView, CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from .models import Pharmacy, Medication, Sale, SaleItem, models, DOSAGE_FORMS, Supplier, PharmacyProduct
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from rest_framework import status
from .serializers import MedicationSerializer
import json
from django.core.cache import cache
from django.contrib import messages
from django.urls import reverse_lazy

# Create your views here.

class BasePharmacyView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Base view for handling pharmacy-related views."""

    def test_func(self) -> bool | None:
        pharmacy_id = self.kwargs.get('pharmacy_id')
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
        return pharmacy in self.request.user.pharmacies.all() or self.request.user.is_superuser
    
    def get_pharmacy(self):
        """Retrieve the pharmacy object."""
        return get_object_or_404(Pharmacy, id=self.kwargs['pharmacy_id'])
    
    def get_context_data(self, **kwargs):
        """Add the pharmacy to the context."""
        context = super().get_context_data(**kwargs)
        context['pharmacy'] = self.get_pharmacy()
        return context

class IndexView(TemplateView):
    template_name = 'base.html'


class Home(LoginRequiredMixin,TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['pharmacies'] = self.request.user.pharmacies.all()
        return context

class Work(BasePharmacyView,TemplateView):
    template_name = 'core/work.html'

class StaffProductsAdd(LoginRequiredMixin,UserPassesTestMixin,TemplateView):
    template_name = 'core/staff_products_add.html'

    def test_func(self) -> bool | None:
        return self.request.user.is_superuser
    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["dosage_forms"] = DOSAGE_FORMS
        return context
    
### ADD a search bar to search for already added products
class PharmacistProductAdd(BasePharmacyView,TemplateView):
    template_name = 'core/pharmacist_products_add.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pharmacy = self.get_pharmacy()
        context['pharmacy'] = pharmacy
        context["dosage_forms"] = DOSAGE_FORMS
        context["suppliers"] = pharmacy.suppliers.all()
        return context
    
class SalesListView(BasePharmacyView,ListView):
    model = Sale
    template_name = 'core/sale_list.html'
    context_object_name = 'sales'
    
    def get_queryset(self):
        pharmacy = self.get_pharmacy()
        query = cache.get('sales_metrics')
        query = self.model.objects.filter(pharmacy=pharmacy).order_by('-created_at')
        return query

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        pharmacy_id = self.kwargs.get('pharmacy_id')    
        pharmacy = self.get_pharmacy()

        if pharmacy.has_feature('basic_selling_metrics'):
            metrics = cache.get(f'{pharmacy_id}-sales_metrics')
            if not metrics:
                pharmacy_sales = self.model.objects.filter(pharmacy=pharmacy)
                total_sales_count = pharmacy_sales.count()
                total_sales_amount = pharmacy_sales.aggregate(total=models.Sum('total_amount'))['total'] or 0
                total_discount = pharmacy_sales.aggregate(total=models.Sum('discount'))['total'] or 0
                total_payment_received = pharmacy_sales.aggregate(total=models.Sum('payment_received'))['total'] or 0

                average_sale_amount = round((total_sales_amount / total_sales_count if total_sales_count > 0 else 0),3)

                best_selling_product_item = (
                    SaleItem.objects.filter(sale__pharmacy=pharmacy).values('product__product__name')
                    .annotate(total_sales=models.Sum('price'))
                    .order_by('-total_sales')
                    .first()
                )
                best_selling_product = best_selling_product_item['product__product__name'] if best_selling_product_item else "None"
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
            context['has_metrics_feature'] = True
        else:
            context["metrics"] = True
        return context
    
class SupplierCreateView(BasePharmacyView, CreateView):
    model = Supplier
    template_name = "core/add_supplier.html"
    fields = ['name','office','contact_info']
    
    def form_valid(self, form):
        form.instance.pharmacy = self.get_pharmacy()
        messages.success(self.request, "Supplier added successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("Work", kwargs={"pharmacy_id": self.kwargs['pharmacy_id']})
    

class InventoryView(BasePharmacyView, TemplateView):
    template_name = 'core/inventory.html'

    def get(self, request, pharmacy_id):
        """Handle GET requests to display the inventory."""
        products = self.get_filtered_products(request)
        page_obj = self.paginate_products(products, request)
        return render(request, self.template_name, self.get_context_data(page_obj=page_obj))

    def get_context_data(self, **kwargs):
        """Add additional context for the inventory view."""
        context = super().get_context_data(**kwargs)
        pharmacy = self.get_pharmacy()
        context['current_sort'] = self.request.GET.get('sort', 'name')
        context['search_query'] = self.request.GET.get('search', '')
        if pharmacy.has_feature("basic_inventory_audit"):
            context['show_expired'] = self.request.GET.get('show_expired','false') == 'true'
            context['has_basic_inventory_audit'] = True
            context['today'] = timezone.now().date()
            context['soon'] = timezone.now().date() + timedelta(days=30)
        context['products'] = kwargs.get('page_obj')
        return context
        
    def get_filtered_products(self, request):
        """Retrieve filtered products based on search and sorting."""
        pharmacy = self.get_pharmacy()
        products = PharmacyProduct.objects.select_related('product', 'supplier').filter(pharmacy=pharmacy)

        search_query = request.GET.get('search', '')
        if search_query:
            products = products.filter(product__name__icontains=search_query)

        show_expired = request.GET.get('show_expired') == 'true'
        if show_expired:
            products = products.filter(expiration_date__lt=timezone.now(), stock_level__gt=0)

        sort_by = request.GET.get('sort', 'name')
        if sort_by == 'price':
            products = products.order_by('price')
        elif sort_by == 'stock_level':
            products = products.order_by('stock_level')
        else:
            products = products.order_by('product__name')

        return products

    def paginate_products(self, products, request):
        """Paginate the product list."""
        paginator = Paginator(products, 30)
        page_number = request.GET.get('page', 1)
        return paginator.get_page(page_number)
