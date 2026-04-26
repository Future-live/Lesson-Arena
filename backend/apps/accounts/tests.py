from rest_framework import status
from rest_framework.test import APITestCase


class AuthApiTests(APITestCase):
    def test_register_and_login(self):
        register_response = self.client.post(
            "/api/auth/register/",
            {
                "username": "teacher_a",
                "email": "teacher_a@example.com",
                "display_name": "教师A",
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!",
                "organization": "示例学校",
                "title": "语文教师",
                "role": "teacher",
            },
            format="json",
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)

        login_response = self.client.post(
            "/api/auth/login/",
            {"username": "teacher_a", "password": "StrongPass123!"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_response.data)
        self.assertEqual(login_response.data["user"]["display_name"], "教师A")
