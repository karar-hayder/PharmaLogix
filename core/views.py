from typing import Any
from django.shortcuts import render
from django.views.generic import TemplateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Pharmacy, Medication
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from rest_framework import status
from .serializers import MedicationSerializer
import json
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