# Doctor record. Doctors are a shared directory: everyone can read them, but
# only the user who added a doctor can change or remove it.
from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import models

from core.models import TimeStampedModel
from core.validators import phone_validator


class Doctor(TimeStampedModel):
    name = models.CharField(max_length=150)
    specialization = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, validators=[phone_validator])
    experience_years = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(70)])
    is_available = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="doctors"
    )

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return f"Dr. {self.name} ({self.specialization})"
