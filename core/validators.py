# Reusable field validators shared by the patient and doctor models.
from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    regex=r"^\+?[0-9 \-]{7,20}$",
    message="Enter a valid phone number (7-20 digits, optional leading +, spaces or dashes).",
)
