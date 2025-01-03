from django.urls import path
from django.contrib.auth.views import LoginView
from . import views

urlpatterns = [
    path("users/login/",LoginView.as_view(template_name='users/login.html'),name='Login'),
    path("staff/pharmacies/",views.PharmacyList.as_view(),name="Staff pharmacies list"),
    path("staff/pharmacies/subscribe/<int:pharmacy_id>/",views.ChoosePlanView.as_view(),name="Staff pharmacies subscribe")
]
