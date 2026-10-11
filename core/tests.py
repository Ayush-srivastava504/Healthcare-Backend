# Tests for the shared pieces: the stats endpoint and the error format.
from .test_utils import BaseAPITestCase


class StatsTests(BaseAPITestCase):
    def test_stats_reflect_the_users_data(self):
        user = self.sign_in()
        from mappings.models import PatientDoctorMapping

        covered = self.make_patient(user, name="Covered")
        self.make_patient(user, name="Alone")
        cardio = self.make_doctor(user, specialization="Cardiology")
        self.make_doctor(user, specialization="Cardiology", is_available=False)
        PatientDoctorMapping.objects.create(patient=covered, doctor=cardio, is_primary=True)

        response = self.client.get("/api/stats/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["patients"], {"total": 2, "without_doctor": 1})
        self.assertEqual(response.data["doctors"]["total"], 2)
        self.assertEqual(response.data["doctors"]["available"], 1)
        self.assertEqual(
            response.data["doctors"]["by_specialization"],
            [{"specialization": "Cardiology", "total": 2}],
        )
        self.assertEqual(response.data["mappings"], {"total": 1, "with_primary_doctor": 1})


class ErrorFormatTests(BaseAPITestCase):
    def test_unauthenticated_error_shape(self):
        response = self.client.get("/api/patients/")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(set(response.data), {"status_code", "message", "errors"})
        self.assertIsNone(response.data["errors"])

    def test_validation_error_shape(self):
        self.sign_in()
        response = self.client.post("/api/patients/", {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["message"], "Validation failed.")
        self.assertIn("name", response.data["errors"])
