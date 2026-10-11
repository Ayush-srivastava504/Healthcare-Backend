# Patient endpoints. Both views are scoped to the logged-in user, so someone
# else's patient simply looks like it does not exist (404).
from rest_framework import generics

from core.mixins import CreatedByMixin, OwnerScopedMixin

from .filters import PatientFilter
from .models import Patient
from .serializers import PatientSerializer


class PatientListCreateView(OwnerScopedMixin, CreatedByMixin, generics.ListCreateAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    filterset_class = PatientFilter
    search_fields = ("name", "phone")
    ordering_fields = ("name", "age", "created_at")


class PatientDetailView(OwnerScopedMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
