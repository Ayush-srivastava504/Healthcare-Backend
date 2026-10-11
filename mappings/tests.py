# Mapping tests: assignment rules, ownership, lookups by patient, primary
# doctor handling and removal.
from core.test_utils import BaseAPITestCase

from .models import PatientDoctorMapping

URL = "/api/mappings/"


class MappingAPITests(BaseAPITestCase):
    def setUp(self):
        self.owner = self.sign_in()
        self.patient = self.make_patient(self.owner)
        self.doctor = self.make_doctor(self.owner)

    def assign(self, **extra):
        data = {"patient": self.patient.id, "doctor": self.doctor.id, **extra}
        return self.client.post(URL, data, format="json")

    def test_assign_a_doctor(self):
        response = self.assign(notes="Follow-up in June")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["doctor_name"], "Gregory House")
        self.assertEqual(response.data["notes"], "Follow-up in June")
        self.assertFalse(response.data["is_primary"])

    def test_duplicate_assignment_is_rejected(self):
        self.assign()
        response = self.assign()
        self.assertEqual(response.status_code, 400)
        self.assertIn("already assigned", str(response.data["errors"]))

    def test_unknown_or_unavailable_doctor_is_rejected(self):
        self.assertEqual(self.client.post(URL, {"patient": self.patient.id, "doctor": 9999}, format="json").status_code, 400)
        away = self.make_doctor(self.owner, is_available=False)
        response = self.client.post(URL, {"patient": self.patient.id, "doctor": away.id}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("doctor", response.data["errors"])

    def test_cannot_assign_to_someone_elses_patient(self):
        stranger = self.make_patient(self.create_user("bob@example.com", "Bob"))
        response = self.client.post(URL, {"patient": stranger.id, "doctor": self.doctor.id}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("patient", response.data["errors"])

    def test_list_only_shows_mappings_of_own_patients(self):
        self.assign()
        other = self.create_user("bob@example.com", "Bob")
        PatientDoctorMapping.objects.create(patient=self.make_patient(other), doctor=self.doctor)
        self.assertEqual(len(self.client.get(URL).data), 1)
        self.assertEqual(len(self.client.get(URL, {"doctor": self.doctor.id}).data), 1)
        self.assertEqual(len(self.client.get(URL, {"is_primary": "true"}).data), 0)

    def test_doctors_of_a_patient(self):
        second = self.make_doctor(self.owner, name="Lisa Cuddy")
        self.assign()
        self.client.post(URL, {"patient": self.patient.id, "doctor": second.id}, format="json")

        response = self.client.get(f"{URL}{self.patient.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual({m["doctor_name"] for m in response.data}, {"Gregory House", "Lisa Cuddy"})

    def test_doctors_of_someone_elses_patient_is_404(self):
        stranger = self.make_patient(self.create_user("bob@example.com", "Bob"))
        self.assertEqual(self.client.get(f"{URL}{stranger.id}/").status_code, 404)

    def test_only_one_primary_doctor_per_patient(self):
        second = self.make_doctor(self.owner)
        self.assertEqual(self.assign(is_primary=True).status_code, 201)
        response = self.client.post(URL, {"patient": self.patient.id, "doctor": second.id, "is_primary": True}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("primary doctor", str(response.data["errors"]))

    def test_patch_updates_notes_and_primary_flag_only(self):
        mapping_id = self.assign().data["id"]
        other_doctor = self.make_doctor(self.owner)
        response = self.client.patch(
            f"{URL}{mapping_id}/",
            {"is_primary": True, "notes": "Lead physician", "doctor": other_doctor.id},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data["is_primary"])
        self.assertEqual(response.data["doctor"], self.doctor.id)

    def test_delete_mapping(self):
        mapping_id = self.assign().data["id"]
        self.assertEqual(self.client.delete(f"{URL}{mapping_id}/").status_code, 204)
        self.assertEqual(len(self.client.get(f"{URL}{self.patient.id}/").data), 0)

    def test_cannot_delete_or_edit_other_users_mapping(self):
        mapping_id = self.assign().data["id"]
        self.sign_in(self.create_user("bob@example.com", "Bob"))
        self.assertEqual(self.client.delete(f"{URL}{mapping_id}/").status_code, 404)
        self.assertEqual(self.client.patch(f"{URL}{mapping_id}/", {"notes": "x"}, format="json").status_code, 404)
