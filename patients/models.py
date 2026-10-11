# Patient record. Each patient belongs to the user who created it and is only
# ever visible to that user.
from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import models

from core.models import TimeStampedModel
from core.validators import phone_validator


class Patient(TimeStampedModel):
    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        OTHER = "O", "Other"

    class BloodGroup(models.TextChoices):
        A_POS = "A+", "A+"
        A_NEG = "A-", "A-"
        B_POS = "B+", "B+"
        B_NEG = "B-", "B-"
        AB_POS = "AB+", "AB+"
        AB_NEG = "AB-", "AB-"
        O_POS = "O+", "O+"
        O_NEG = "O-", "O-"

    name = models.CharField(max_length=150)
    age = models.PositiveSmallIntegerField(validators=[MaxValueValidator(130)])
    gender = models.CharField(max_length=1, choices=Gender.choices)
    blood_group = models.CharField(max_length=3, choices=BloodGroup.choices, blank=True)
    phone = models.CharField(max_length=20, blank=True, validators=[phone_validator])
    address = models.TextField(blank=True)
    medical_history = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="patients"
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.name
