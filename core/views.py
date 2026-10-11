# A small dashboard endpoint: headline numbers for the logged-in user.
from django.db.models import Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from doctors.models import Doctor
from mappings.models import PatientDoctorMapping
from patients.models import Patient


class StatsView(APIView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        patients = Patient.objects.filter(created_by=request.user)
        mappings = PatientDoctorMapping.objects.filter(patient__created_by=request.user)
        specializations = (
            Doctor.objects.values("specialization")
            .annotate(total=Count("id"))
            .order_by("-total", "specialization")
        )

        return Response(
            {
                "patients": {
                    "total": patients.count(),
                    "without_doctor": patients.filter(mappings__isnull=True).count(),
                },
                "doctors": {
                    "total": Doctor.objects.count(),
                    "available": Doctor.objects.filter(is_available=True).count(),
                    "by_specialization": list(specializations),
                },
                "mappings": {
                    "total": mappings.count(),
                    "with_primary_doctor": mappings.filter(is_primary=True).count(),
                },
            }
        )
