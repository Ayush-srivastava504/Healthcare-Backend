# Auth tests: registration rules, token login, logout (blacklisting),
# profile updates and password changes.
from django.contrib.auth.models import User

from core.test_utils import BaseAPITestCase

REGISTER = "/api/auth/register/"
LOGIN = "/api/auth/login/"


class RegistrationTests(BaseAPITestCase):
    def payload(self, **overrides):
        data = {"name": "Alice", "email": "Alice@Example.com", "password": self.password}
        data.update(overrides)
        return data

    def test_register_creates_user_and_normalises_email(self):
        response = self.client.post(REGISTER, self.payload(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["email"], "alice@example.com")
        self.assertNotIn("password", response.data)
        self.assertTrue(User.objects.filter(username="alice@example.com").exists())

    def test_duplicate_email_is_rejected_case_insensitively(self):
        self.client.post(REGISTER, self.payload(), format="json")
        response = self.client.post(REGISTER, self.payload(email="ALICE@example.com"), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data["errors"])

    def test_weak_password_and_bad_email_are_rejected(self):
        response = self.client.post(REGISTER, self.payload(email="nope", password="123"), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data["errors"])
        self.assertIn("password", response.data["errors"])

    def test_missing_fields_are_reported(self):
        response = self.client.post(REGISTER, {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.data["errors"]), {"name", "email", "password"})


class LoginTests(BaseAPITestCase):
    def test_login_returns_tokens_that_work(self):
        self.create_user()
        response = self.client.post(LOGIN, {"email": "alice@example.com", "password": self.password}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["name"], "Alice")

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        self.assertEqual(self.client.get("/api/patients/").status_code, 200)

    def test_wrong_password_is_rejected(self):
        self.create_user()
        response = self.client.post(LOGIN, {"email": "alice@example.com", "password": "wrong"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_protected_routes_need_a_token(self):
        self.assertEqual(self.client.get("/api/doctors/").status_code, 401)


class SessionTests(BaseAPITestCase):
    def test_logout_blacklists_the_refresh_token(self):
        self.create_user()
        tokens = self.client.post(LOGIN, {"email": "alice@example.com", "password": self.password}, format="json").data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        self.assertEqual(self.client.post("/api/auth/logout/", {"refresh": tokens["refresh"]}, format="json").status_code, 204)

        self.client.credentials()
        response = self.client.post("/api/auth/token/refresh/", {"refresh": tokens["refresh"]}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_logout_with_garbage_token(self):
        self.sign_in()
        response = self.client.post("/api/auth/logout/", {"refresh": "garbage"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_profile_read_and_update(self):
        self.sign_in()
        self.assertEqual(self.client.get("/api/auth/me/").data["email"], "alice@example.com")
        response = self.client.patch("/api/auth/me/", {"name": "Alice B", "email": "hacker@x.com"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Alice B")
        self.assertEqual(response.data["email"], "alice@example.com")

    def test_change_password(self):
        user = self.sign_in()
        wrong = self.client.post("/api/auth/change-password/", {"old_password": "bad", "new_password": "An0ther!Pass987"}, format="json")
        self.assertEqual(wrong.status_code, 400)

        ok = self.client.post("/api/auth/change-password/", {"old_password": self.password, "new_password": "An0ther!Pass987"}, format="json")
        self.assertEqual(ok.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password("An0ther!Pass987"))
