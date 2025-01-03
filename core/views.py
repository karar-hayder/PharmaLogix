from typing import Any
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render
from django.views.generic import TemplateView, ListView, CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from .models import Pharmacy, Sale, SaleItem, DOSAGE_FORMS, Supplier, PharmacyProduct
from django.shortcuts import get_object_or_404
from datetime import datetime
from django.core.cache import cache
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Sum
from .extras import hash_key
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
    
class SalesListView(BasePharmacyView, ListView):
    model = Sale
    template_name = 'core/sale_list.html'
    context_object_name = 'sales'
    
    def get_queryset(self):
        pharmacy = self.get_pharmacy()
        selected_date = self.request.GET.get('date', timezone.localdate())
        
        if isinstance(selected_date, str):
            try:
                selected_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
            except ValueError:
                selected_date = timezone.localdate()
        
        cache_key = hash_key(f"{pharmacy.id}-sales_query-{selected_date}")
        queryset = cache.get(cache_key)
        if not queryset:
            queryset = self.model.objects.filter(
                pharmacy=pharmacy,
                created_at__date=selected_date
            ).order_by('-created_at')
            cache.set(cache_key, queryset, timeout=60 * 5)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pharmacy = self.get_pharmacy()
        pharmacy_id = self.kwargs.get('pharmacy_id')
        
        selected_date = self.request.GET.get('date', timezone.localdate())
        if isinstance(selected_date, str):
            try:
                selected_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
            except ValueError:
                selected_date = timezone.localdate()
        
        context['selected_date'] = selected_date
        
        if pharmacy.has_feature('basic_selling_metrics'):
            cache_key = hash_key(f"{pharmacy_id}-sales_metrics-{selected_date}")
            metrics = cache.get(cache_key)
            if not metrics:
                daily_sales = self.model.objects.filter(
                    pharmacy=pharmacy,
                    created_at__date=selected_date
                )
                total_sales_count = daily_sales.count()
                total_sales_amount = daily_sales.aggregate(total=Sum('total_amount'))['total'] or 0
                total_discount = daily_sales.aggregate(total=Sum('discount'))['total'] or 0
                total_payment_received = daily_sales.aggregate(total=Sum('payment_received'))['total'] or 0
                average_sale_amount = round((total_sales_amount / total_sales_count if total_sales_count > 0 else 0), 3)

                best_selling_product_item = (
                    SaleItem.objects.filter(sale__pharmacy=pharmacy, sale__created_at__date=selected_date)
                    .values('product__product__name')
                    .annotate(total_sales=Sum('price'))
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

                cache.set(cache_key, metrics, timeout=60 * 5)
            
            context['metrics'] = metrics
            context['has_metrics_feature'] = True
            context['has_advanced_metrics'] = pharmacy.has_feature('advanced_selling_metrics')
        else:
            context['metrics'] = None
        
        return context
    
class SupplierCreateView(BasePharmacyView, CreateView):
    model = Supplier
    template_name = "core/add_supplier.html"
    fields = ['office','contact_info']
    
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
            if pharmacy.has_feature("advnaced_inventory_audit"):
                context['has_advanced_inventory_audit'] = True
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

class AdvancedSalesMetricsView(BasePharmacyView, TemplateView):
    template_name = 'core/advanced_sales_metrics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pharmacy_id = self.kwargs.get('pharmacy_id')
        pharmacy = self.get_pharmacy()
        
        if pharmacy.has_feature('advanced_selling_metrics'):
            start_date = self.request.GET.get('start_date')
            end_date = self.request.GET.get('end_date')
            
            if start_date:
                start_date = timezone.datetime.strptime(start_date, "%Y-%m-%d").date()
            else:
                start_date = timezone.now().date() - timedelta(days=30)
            
            if end_date:
                end_date = timezone.datetime.strptime(end_date, "%Y-%m-%d").date()
            else:
                end_date = timezone.now().date()

            cache_key = hash_key(f'{pharmacy_id}-advanced_sales_metrics-{start_date}-{end_date}')
            metrics = cache.get(cache_key)
            if not metrics:
                pharmacy_sales = Sale.objects.filter(
                    pharmacy=pharmacy,
                    created_at__date__range=(start_date, end_date)
                )
                
                total_sales_count = pharmacy_sales.count()
                total_sales_amount = pharmacy_sales.aggregate(total=Sum('total_amount'))['total'] or 0
                total_discount = pharmacy_sales.aggregate(total=Sum('discount'))['total'] or 0
                total_payment_received = pharmacy_sales.aggregate(total=Sum('payment_received'))['total'] or 0
                average_sale_amount = round((total_sales_amount / total_sales_count if total_sales_count > 0 else 0), 3)

                best_selling_product_item = (
                    SaleItem.objects.filter(sale__pharmacy=pharmacy, sale__created_at__date__range=(start_date, end_date))
                    .values('product__product__name')
                    .annotate(total_sales=Sum('price'))
                    .order_by('-total_sales')
                    .first()
                )
                best_selling_product = best_selling_product_item['product__product__name'] if best_selling_product_item else "None"
                best_selling_product_revenue = best_selling_product_item['total_sales'] if best_selling_product_item else 0


                sales_dates = []
                sales_amount_data = []

                current_date = start_date
                while current_date <= end_date:
                    total_for_date = Sale.objects.filter(
                        pharmacy=pharmacy,
                        created_at__date=current_date
                    ).aggregate(total=Sum('total_amount'))['total'] or 0
                    sales_dates.append(current_date.strftime('%Y-%m-%d'))
                    sales_amount_data.append(total_for_date)
                    current_date += timedelta(days=1)

                best_selling_products = (
                    SaleItem.objects.filter(sale__pharmacy=pharmacy, sale__created_at__date__range=(start_date, end_date))
                    .values('product__product__name')
                    .annotate(total_sales=Sum('price'))
                    .order_by('-total_sales')[:10]
                )
                best_selling_product_names = [item['product__product__name'] for item in best_selling_products]
                best_selling_product_revenues = [item['total_sales'] for item in best_selling_products]

                pharmacist_sales_data = (
                    SaleItem.objects.filter(sale__pharmacy=pharmacy, sale__created_at__date__range=(start_date, end_date))
                    .values('sale__pharmacist__first_name')
                    .annotate(total_sales=Sum('price'))
                    .order_by('-total_sales')
                )
                pharmacist_sales_data_dict = {
                    pharmacist['sale__pharmacist__first_name']: pharmacist['total_sales']
                    for pharmacist in pharmacist_sales_data
                }

                previous_period_start = start_date - timedelta(days=(end_date - start_date).days + 1)
                previous_period_end = start_date - timedelta(days=1)
                previous_sales_total = Sale.objects.filter(
                    pharmacy=pharmacy,
                    created_at__date__range=(previous_period_start, previous_period_end)
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                sales_growth = (
                    ((total_sales_amount - previous_sales_total) / previous_sales_total * 100)
                    if previous_sales_total > 0 else 0
                )
                
                # forecasted_sales = total_sales_amount * (1 + sales_growth)
                growth_rate = 0.05
                today = timezone.now()
                same_month_last_year_start = today.replace(year=today.year - 1, day=1)
                same_month_last_year_end = (same_month_last_year_start + timedelta(days=30))
                last_year_sales_for_same_month = pharmacy_sales.filter(
                    created_at__gte=same_month_last_year_start,
                    created_at__lt=same_month_last_year_end
                ).aggregate(total=Sum('total_amount'))['total'] or 0


                forecasted_sales = last_year_sales_for_same_month * (1 + growth_rate)
                metrics = {
                    'total_sales_count': total_sales_count,
                    'total_sales_amount': f"{total_sales_amount} IQD",
                    'total_discount': f"{total_discount} IQD",
                    'total_payment_received': f"{total_payment_received} IQD",
                    'average_sale_amount': f"{average_sale_amount} IQD",
                    'best_selling_product': best_selling_product,
                    'best_selling_product_revenue': f"{best_selling_product_revenue} IQD",
                    'forecasted_sales': f"{round(forecasted_sales, 4)} IQD",
                    'sales_dates': sales_dates,
                    'sales_amount_data': sales_amount_data,
                    'best_selling_product_names': best_selling_product_names,
                    'best_selling_product_revenues': best_selling_product_revenues,
                    'pharmacist_sales_data': pharmacist_sales_data_dict,
                    'sales_growth': round(sales_growth, 2),
                }
                cache.set(cache_key, metrics, timeout=60*5)

            context["metrics"] = metrics
        else:
            context["metrics"] = False
        
        return context