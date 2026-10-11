from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from core.mixins import CreatedByMixin

from .filters import DoctorFilter
from .models import Doctor
from .permissions import IsCreatorOrReadOnly
from .serializers import DoctorSerializer


class DoctorListCreateView(CreatedByMixin, generics.ListCreateAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    filterset_class = DoctorFilter
    search_fields = ("name", "specialization")
    ordering_fields = ("name", "experience_years", "created_at")


class DoctorDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = (IsAuthenticated, IsCreatorOrReadOnly)
