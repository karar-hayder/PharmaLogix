from django.urls import path, include
from . import views

from rest_framework.routers import DefaultRouter
from .API_views import MedicationViewSet, CosmeticViewSet, ProductViewSet,PharmacyProductSearchAPIView, CartAPIView, CheckoutAPIView, CreateProductAndPharmacyProductView

router = DefaultRouter()
router.register(r'medication', MedicationViewSet, basename='medication')
router.register(r'cosmetic', CosmeticViewSet, basename='cosmetic')
router.register(r'product', ProductViewSet, basename='product')

urlpatterns = [

    ## Main ##
    path('',views.Home.as_view(),name='Main'),
    path('work/<int:pharmacy_id>/',views.Work.as_view(),name='Work'),
    path('staff/products/add/',views.StaffProductsAdd.as_view(),name='Barcode add'),
    path('product/<int:pharmacy_id>/add/',views.PharmacistProductAdd.as_view(),name='Product add'),
    path('sale/<int:pharmacy_id>/list/',views.SalesListView.as_view(),name='Sale list'),

    ## API ##
    path('api/', include(router.urls)),
    # path('api/meds/create/',API_views.MedicationCreateView.as_view(),name="Med create"),
    path('api/pharmacy/<int:pharmacy_id>/cart/', CartAPIView.as_view(), name='cart'),
    path('api/pharmacy/<int:pharmacy_id>/cart/<int:product_id>/', CartAPIView.as_view(), name='cart'),
    path('api/pharmacy/<int:pharmacy_id>/cart/<int:product_id>/update-quantity/', CartAPIView.as_view()),
    path('api/pharmacy/<int:pharmacy_id>/checkout/', CheckoutAPIView.as_view(), name='checkout'),
    path('api/pharmacy/<int:pharmacy_id>/search/', PharmacyProductSearchAPIView.as_view(), name='product-search'),
    # path('api/pharmacy/<int:pharmacy_id>/update/<int:product_id>/', API_views.ProductUpdateAPIView.as_view(), name='product-update'),
    path('api/pharmacy/<int:pharmacy_id>/add/', CreateProductAndPharmacyProductView.as_view(), name='product-add'),

]
