# Shared helpers for the test suites: quick user / patient / doctor factories
# and a one-liner to sign a user in without going through the login endpoint.
from itertools import count

from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from doctors.models import Doctor
from patients.models import Patient

_doctor_counter = count(1)


class BaseAPITestCase(APITestCase):
    password = "Str0ng!Pass123"

    def create_user(self, email="alice@example.com", name="Alice"):
        return User.objects.create_user(
            username=email, email=email, first_name=name, password=self.password
        )

    def sign_in(self, user=None):
        user = user or self.create_user()
        self.client.force_authenticate(user=user)
        return user

    def make_patient(self, owner, **overrides):
        data = {"name": "John Doe", "age": 40, "gender": "M"}
        data.update(overrides)
        return Patient.objects.create(created_by=owner, **data)

    def make_doctor(self, owner, **overrides):
        data = {
            "name": "Gregory House",
            "specialization": "Diagnostics",
            "email": f"doctor{next(_doctor_counter)}@hospital.com",
        }
        data.update(overrides)
        return Doctor.objects.create(created_by=owner, **data)
