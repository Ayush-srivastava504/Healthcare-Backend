# Mapping serializers. Business rules live here: you can only assign doctors
# to your own patients, unavailable doctors cannot be assigned, and a patient
# can have only one primary doctor.
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .models import PatientDoctorMapping


class MappingSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.name", read_only=True)
    doctor_specialization = serializers.CharField(source="doctor.specialization", read_only=True)

    class Meta:
        model = PatientDoctorMapping
        fields = (
            "id",
            "patient",
            "patient_name",
            "doctor",
            "doctor_name",
            "doctor_specialization",
            "is_primary",
            "notes",
            "assigned_at",
        )
        read_only_fields = ("id", "assigned_at")
        validators = [
            UniqueTogetherValidator(
                queryset=PatientDoctorMapping.objects.all(),
                fields=("patient", "doctor"),
                message="This doctor is already assigned to this patient.",
            )
        ]

    def validate_patient(self, patient):
        if patient.created_by_id != self.context["request"].user.id:
            raise serializers.ValidationError("Patient not found.")
        return patient

    def validate_doctor(self, doctor):
        if not doctor.is_available:
            raise serializers.ValidationError("This doctor is not accepting new patients.")
        return doctor

    def validate(self, attrs):
        patient = attrs.get("patient") or self.instance.patient
        if attrs.get("is_primary"):
            clashes = PatientDoctorMapping.objects.filter(patient=patient, is_primary=True)
            if self.instance:
                clashes = clashes.exclude(pk=self.instance.pk)
            if clashes.exists():
                raise serializers.ValidationError("This patient already has a primary doctor.")
        return attrs


class MappingUpdateSerializer(MappingSerializer):
    class Meta(MappingSerializer.Meta):
        read_only_fields = ("id", "patient", "doctor", "assigned_at")
        validators = []
