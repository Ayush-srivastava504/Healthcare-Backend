import django_filters

from .models import Doctor


class DoctorFilter(django_filters.FilterSet):
    specialization = django_filters.CharFilter(lookup_expr="icontains")
    min_experience = django_filters.NumberFilter(field_name="experience_years", lookup_expr="gte")

    class Meta:
        model = Doctor
        fields = ("specialization", "is_available")
