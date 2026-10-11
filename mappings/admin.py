from django.contrib import admin

from .models import PatientDoctorMapping


@admin.register(PatientDoctorMapping)
class PatientDoctorMappingAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "is_primary", "assigned_at")
    list_filter = ("is_primary",)
    search_fields = ("patient__name", "doctor__name")
