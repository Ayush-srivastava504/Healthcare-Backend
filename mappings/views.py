# Mapping endpoints. The detail route is shared by three actions to match the
# assignment's URL design: GET reads by patient id, while PATCH and DELETE
# act on the mapping id.
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response

from core.mixins import OwnerScopedMixin
from patients.models import Patient

from .models import PatientDoctorMapping
from .serializers import MappingSerializer, MappingUpdateSerializer

MAPPING_QUERYSET = PatientDoctorMapping.objects.select_related("patient", "doctor")


class MappingListCreateView(OwnerScopedMixin, generics.ListCreateAPIView):
    queryset = MAPPING_QUERYSET
    owner_lookup = "patient__created_by"
    serializer_class = MappingSerializer
    filterset_fields = ("patient", "doctor", "is_primary")
    search_fields = ("patient__name", "doctor__name")
    ordering_fields = ("assigned_at",)


class MappingDetailView(OwnerScopedMixin, generics.GenericAPIView):
    queryset = MAPPING_QUERYSET
    owner_lookup = "patient__created_by"

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return MappingUpdateSerializer
        return MappingSerializer

    @extend_schema(operation_id="mappings_by_patient", responses=MappingSerializer(many=True))
    def get(self, request, pk):
        patient = get_object_or_404(Patient, pk=pk, created_by=request.user)
        mappings = self.get_queryset().filter(patient=patient)
        return Response(MappingSerializer(mappings, many=True).data)

    def patch(self, request, pk):
        mapping = self.get_object()
        serializer = self.get_serializer(mapping, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
