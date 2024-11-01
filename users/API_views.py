from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Supplier, Pharmacy
from .serializers import SupplierSerializer

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        pharmacy_id = self.request.query_params.get('pharmacy_id')
        user = self.request.user
        
        if pharmacy_id:
            pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id, owner=user)
            return self.queryset.filter(pharmacy=pharmacy)
        
        return self.queryset.none()

    def perform_create(self, serializer):
        pharmacy_id = self.request.data.get('pharmacy_id')
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id, owner=self.request.user)

        serializer.save(pharmacy=pharmacy)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        if instance.pharmacy.owner != request.user:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.pharmacy.owner != request.user:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def list_for_pharmacy(self, request):
        pharmacy_id = request.query_params.get('pharmacy_id')
        if not pharmacy_id:
            return Response({"detail": "pharmacy_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id, owner=request.user)
        suppliers = self.queryset.filter(pharmacy=pharmacy)
        serializer = self.get_serializer(suppliers, many=True)
        
        return Response(serializer.data)
