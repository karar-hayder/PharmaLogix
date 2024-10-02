from typing import Any
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.


class IndexView(TemplateView):
    template_name = 'base.html'


class Home(LoginRequiredMixin,TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['pharmacies'] = self.request.user.pharmacies.all()
        return context
