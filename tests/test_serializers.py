from django.contrib.auth.models import User
from django.test import TestCase

from users.models import UserProfile
from users.serializers import SignupSerializer


class SignupSerializerTests(TestCase):

    def test_valid_signup_data(self):
        data = {
            "email": "test@example.com",
            "password": "StrongPassword123!",
            "role": UserProfile.Role.SEEKER,
        }

        serializer = SignupSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data["email"],
            "test@example.com",
        )
        self.assertEqual(
            serializer.validated_data["role"],
            UserProfile.Role.SEEKER,
        )

    def test_email_is_normalized(self):
        data = {
            "email": "  TEST@Example.COM  ",
            "password": "StrongPassword123!",
            "role": UserProfile.Role.SEEKER,
        }

        serializer = SignupSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data["email"],
            "test@example.com",
        )

    def test_invalid_email_is_rejected(self):
        data = {
            "email": "not-an-email",
            "password": "StrongPassword123!",
            "role": UserProfile.Role.SEEKER,
        }

        serializer = SignupSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_email_is_required(self):
        data = {
            "password": "StrongPassword123!",
            "role": UserProfile.Role.SEEKER,
        }

        serializer = SignupSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_password_is_required(self):
        data = {
            "email": "test@example.com",
            "role": UserProfile.Role.SEEKER,
        }

        serializer = SignupSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_password_minimum_length(self):
        data = {
            "email": "test@example.com",
            "password": "short",
            "role": UserProfile.Role.SEEKER,
        }

        serializer = SignupSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_role_is_required(self):
        data = {
            "email": "test@example.com",
            "password": "StrongPassword123!",
        }

        serializer = SignupSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("role", serializer.errors)

    def test_invalid_role_is_rejected(self):
        data = {
            "email": "test@example.com",
            "password": "StrongPassword123!",
            "role": "Admin",
        }

        serializer = SignupSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("role", serializer.errors)

    def test_username_is_not_required(self):
        data = {
            "email": "test@example.com",
            "password": "StrongPassword123!",
            "role": UserProfile.Role.SEEKER,
        }

        serializer = SignupSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertNotIn("username", serializer.validated_data)

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username="existing",
            email="test@example.com",
            password="StrongPassword123!",
        )

        data = {
            "email": "TEST@example.com",
            "password": "AnotherPassword123!",
            "role": UserProfile.Role.SEEKER,
        }

        serializer = SignupSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_password_is_write_only(self):
        serializer = SignupSerializer()

        self.assertTrue(
            serializer.fields["password"].write_only
        )