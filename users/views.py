from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from django.core.cache import cache

from .models import Pharmacy
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