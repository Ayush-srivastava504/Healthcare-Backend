from django.contrib import admin

from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("name", "age", "gender", "blood_group", "created_by", "created_at")
    list_filter = ("gender", "blood_group")
    search_fields = ("name", "phone")
