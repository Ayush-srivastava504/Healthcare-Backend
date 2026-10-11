# Links a patient to a doctor. A pair can only exist once, and a patient can
# have at most one primary doctor (enforced by a partial unique constraint).
from django.db import models

from doctors.models import Doctor
from patients.models import Patient


class PatientDoctorMapping(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="mappings")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="mappings")
    is_primary = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-assigned_at",)
        constraints = [
            models.UniqueConstraint(fields=["patient", "doctor"], name="unique_patient_doctor"),
            models.UniqueConstraint(
                fields=["patient"],
                condition=models.Q(is_primary=True),
                name="one_primary_doctor_per_patient",
            ),
        ]

    def __str__(self):
        return f"{self.patient} -> {self.doctor}"
