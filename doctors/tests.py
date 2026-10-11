# Doctor API tests: shared read access, creator-only writes, unique emails
# and the specialization / availability filters.
from core.test_utils import BaseAPITestCase

URL = "/api/doctors/"


class DoctorAPITests(BaseAPITestCase):
    def setUp(self):
        self.owner = self.sign_in()
        self.payload = {
            "name": "Gregory House",
            "specialization": "Diagnostics",
            "email": "House@Hospital.com",
            "experience_years": 20,
        }

    def test_create_normalises_email_and_sets_owner(self):
        response = self.client.post(URL, self.payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["email"], "house@hospital.com")
        self.assertEqual(response.data["created_by"], self.owner.id)
        self.assertTrue(response.data["is_available"])

    def test_duplicate_email_is_rejected(self):
        self.client.post(URL, self.payload, format="json")
        response = self.client.post(URL, {**self.payload, "email": "HOUSE@hospital.com"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data["errors"])

    def test_everyone_can_read_but_only_creator_can_write(self):
        doctor = self.make_doctor(self.owner)
        self.sign_in(self.create_user("bob@example.com", "Bob"))

        self.assertEqual(len(self.client.get(URL).data), 1)
        self.assertEqual(self.client.get(f"{URL}{doctor.id}/").status_code, 200)
        self.assertEqual(self.client.put(f"{URL}{doctor.id}/", self.payload, format="json").status_code, 403)
        self.assertEqual(self.client.delete(f"{URL}{doctor.id}/").status_code, 403)

        self.sign_in(self.owner)
        self.assertEqual(self.client.put(f"{URL}{doctor.id}/", {**self.payload, "name": "G. House"}, format="json").status_code, 200)
        self.assertEqual(self.client.delete(f"{URL}{doctor.id}/").status_code, 204)

    def test_update_can_keep_its_own_email(self):
        doctor = self.make_doctor(self.owner, email="keep@hospital.com")
        response = self.client.patch(f"{URL}{doctor.id}/", {"email": "keep@hospital.com", "phone": "+40 700 000 000"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)

    def test_validation_errors(self):
        response = self.client.post(URL, {"name": "X", "specialization": "Y", "email": "bad", "experience_years": 99, "phone": "x"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.data["errors"]), {"email", "experience_years", "phone"})

    def test_filters_and_search(self):
        self.make_doctor(self.owner, name="Ana", specialization="Cardiology", experience_years=15)
        self.make_doctor(self.owner, name="Bob", specialization="Neurology", experience_years=3, is_available=False)
        self.assertEqual(len(self.client.get(URL, {"specialization": "cardio"}).data), 1)
        self.assertEqual(len(self.client.get(URL, {"is_available": "false"}).data), 1)
        self.assertEqual(len(self.client.get(URL, {"min_experience": 10}).data), 1)
        self.assertEqual(self.client.get(URL, {"search": "neuro"}).data[0]["name"], "Bob")
