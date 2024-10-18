from django.urls import path
from . import views
from . import API_views

urlpatterns = [

    ## Main ##
    path('',views.Home.as_view(),name='Main'),
    path('work/<int:pharmacy_id>/',views.Work.as_view(),name='Work'),
    path('medications/add/',views.BarcodeAdderView.as_view(),name='Barcode add'),
    path('Product/<int:pharmacy_id>/add/',views.AddProductsView.as_view(),name='Product add'),
    path('sale/<int:pharmacy_id>/list/',views.SalesListView.as_view(),name='Sale list'),

    ## API ##
    path('api/meds/create/',API_views.MedicationCreateView.as_view(),name="Med create"),
    path('api/medication/search/', API_views.MedicationSearchView.as_view(), name='Med search'),
    path('api/pharmacy/<int:pharmacy_id>/cart/', API_views.CartAPIView.as_view(), name='cart'),
    path('api/pharmacy/<int:pharmacy_id>/cart/<int:product_id>/', API_views.CartAPIView.as_view(), name='cart'),
    path('api/pharmacy/<int:pharmacy_id>/checkout/', API_views.CheckoutAPIView.as_view(), name='checkout'),
    path('api/pharmacy/<int:pharmacy_id>/search/', API_views.ProductSearchAPIView.as_view(), name='product-search'),
    path('api/pharmacy/<int:pharmacy_id>/update/<int:product_id>/', API_views.ProductUpdateAPIView.as_view(), name='product-update'),
    path('api/pharmacy/<int:pharmacy_id>/add/<int:med_id>/', API_views.ProductCreateView.as_view(), name='product-add'),

]
