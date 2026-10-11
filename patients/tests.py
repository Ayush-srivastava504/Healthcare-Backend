# Patient API tests: CRUD, per-user ownership, validation, filtering and the
# opt-in pagination.
from core.test_utils import BaseAPITestCase

URL = "/api/patients/"


class PatientAPITests(BaseAPITestCase):
    def setUp(self):
        self.owner = self.sign_in()

    def test_create_stamps_the_owner(self):
        response = self.client.post(
            URL,
            {"name": "John Doe", "age": 40, "gender": "M", "blood_group": "O+", "phone": "+40 721 000 111"},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["created_by"], self.owner.id)

    def test_list_only_returns_own_patients(self):
        self.make_patient(self.owner, name="Mine")
        self.make_patient(self.create_user("bob@example.com", "Bob"), name="Theirs")
        response = self.client.get(URL)
        self.assertEqual([p["name"] for p in response.data], ["Mine"])

    def test_other_users_patient_is_hidden(self):
        theirs = self.make_patient(self.create_user("bob@example.com", "Bob"))
        self.assertEqual(self.client.get(f"{URL}{theirs.id}/").status_code, 404)
        self.assertEqual(self.client.put(f"{URL}{theirs.id}/", {"name": "x", "age": 1, "gender": "M"}, format="json").status_code, 404)
        self.assertEqual(self.client.delete(f"{URL}{theirs.id}/").status_code, 404)

    def test_update_and_delete(self):
        patient = self.make_patient(self.owner)
        response = self.client.put(f"{URL}{patient.id}/", {"name": "John D", "age": 41, "gender": "M"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["age"], 41)
        self.assertEqual(self.client.delete(f"{URL}{patient.id}/").status_code, 204)
        self.assertEqual(self.client.get(f"{URL}{patient.id}/").status_code, 404)

    def test_validation_errors(self):
        response = self.client.post(
            URL,
            {"name": " ", "age": 200, "gender": "X", "blood_group": "Z", "phone": "abc"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.data["errors"]), {"name", "age", "gender", "blood_group", "phone"})

    def test_filters_and_search(self):
        self.make_patient(self.owner, name="Ana Pop", age=25, gender="F")
        self.make_patient(self.owner, name="Bogdan Ionescu", age=62, gender="M")
        self.assertEqual(len(self.client.get(URL, {"gender": "F"}).data), 1)
        self.assertEqual(len(self.client.get(URL, {"min_age": 30}).data), 1)
        self.assertEqual(self.client.get(URL, {"search": "bogdan"}).data[0]["name"], "Bogdan Ionescu")
        ordered = self.client.get(URL, {"ordering": "-age"}).data
        self.assertEqual([p["age"] for p in ordered], [62, 25])

    def test_pagination_is_opt_in(self):
        for i in range(12):
            self.make_patient(self.owner, name=f"Patient {i}")
        self.assertEqual(len(self.client.get(URL).data), 12)
        page = self.client.get(URL, {"page": 2}).data
        self.assertEqual(page["count"], 12)
        self.assertEqual(len(page["results"]), 2)
