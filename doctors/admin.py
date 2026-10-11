from django.contrib import admin

from .models import Doctor


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("name", "specialization", "email", "experience_years", "is_available")
    list_filter = ("specialization", "is_available")
    search_fields = ("name", "email", "specialization")
