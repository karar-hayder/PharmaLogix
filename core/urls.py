from django.urls import path
from . import views
from . import API_views

urlpatterns = [
    path('',views.Home.as_view(),name='Main'),

]
