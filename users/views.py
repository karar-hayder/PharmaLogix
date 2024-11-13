from typing import Any
from django.views.generic import ListView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.core.cache import cache
from core.extras import hash_key
from .models import Pharmacy, SubscriptionPlan, Subscription
# Create your views here.

class BaseStaffPage(LoginRequiredMixin,UserPassesTestMixin,View):
    perms = []
    permission_denied_message = "You don't have that permission"
    def test_func(self) -> bool | None:
        key = f"{self.request.user.username}-staff-perms"
        check = cache.get(key)
        if not check:
            check = self.request.user.is_staff and self.request.user.has_perms(self.perms)
            cache.set(key,check,60*60)
        return check



class PharmacyList(BaseStaffPage,ListView):
    model = Pharmacy
    template_name = 'users/staff_pharmacy_list.html'
    context_object_name = 'pharmacies'
    ordering = '-created_at'
    paginate_by = 30


class ChoosePlanView(BaseStaffPage,TemplateView):
    template_name = 'users/choose_plan.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        cache_key = hash_key('plans')
        plans = cache.get(cache_key)
        if not plans:
            plans = SubscriptionPlan.objects.all()
            cache.set(cache_key,plans,60*60*6)
        context['plans'] = plans
        return context

    def post(self, request, pharmacy_id, *args, **kwargs):
        plan_id = request.POST.get('plan_id')
        plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
        subscription = Subscription.objects.create(
            pharmacy=pharmacy,
            plan=plan,
            start_date=timezone.now().date(),
            paid=plan.total_price
        )
        cache.delete(f"{pharmacy.pk}-sub")
        messages.success(request, f"Subscription for {plan.name} has been successfully created for {pharmacy.name}.")
    
        return redirect('Staff pharmacies list')