from unittest.mock import patch
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from users.models import EmailOTP


class OTPSecrecyTests(APITestCase):
    """
    Tests for Challenge C requirements:
    - OTP not returned in API responses
    - OTP stored as hash (not plaintext)
    """

    @patch("users.services.send_mail")
    def test_otp_not_returned_in_signup_response(self, mock_send_mail):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("signup"),
                {"email": "test@example.com", "password": "StrongPassword123!", "role": "Seeker"},
                format="json",
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("otp", response.data)
        self.assertNotIn("otp_hash", response.data)

    @patch("users.services.send_mail")
    def test_otp_not_returned_in_verify_response(self, mock_send_mail):
        # Signup to create OTP
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(
                reverse("signup"),
                {"email": "test@example.com", "password": "StrongPassword123!", "role": "Seeker"},
                format="json",
            )
        # Extract OTP from mocked email
        message = mock_send_mail.call_args.kwargs["message"]
        otp = message.split(": ")[1]

        response = self.client.post(
            reverse("verify-email"),
            {"email": "test@example.com", "otp": otp},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("otp", response.data)
        self.assertNotIn("otp_hash", response.data)

    @patch("users.services.send_mail")
    def test_otp_not_returned_in_resend_response(self, mock_send_mail):
        # Signup to create initial OTP
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(
                reverse("signup"),
                {"email": "test@example.com", "password": "StrongPassword123!", "role": "Seeker"},
                format="json",
            )
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("resend-otp"),
                {"email": "test@example.com"},
                format="json",
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("otp", response.data)
        self.assertNotIn("otp_hash", response.data)

    @patch("users.services.send_mail")
    def test_otp_stored_as_hash_not_plaintext(self, mock_send_mail):
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(
                reverse("signup"),
                {"email": "test@example.com", "password": "StrongPassword123!", "role": "Seeker"},
                format="json",
            )
        otp_record = EmailOTP.objects.get(user__email="test@example.com")
        otp_hash = otp_record.otp_hash

        # Ensure it's not a plain 6-digit string
        self.assertFalse(otp_hash.isdigit(), "OTP hash is a plain number – not hashed!")

        # Django hash formats start with algorithm, e.g., "pbkdf2_sha256$..."
        self.assertTrue(
            otp_hash.startswith("pbkdf2_sha256") or
            otp_hash.startswith("argon2") or
            otp_hash.startswith("bcrypt") or
            len(otp_hash) > 20,   # fallback for custom hashers
            f"OTP hash does not look like a Django hash: {otp_hash[:20]}..."
        )

    @patch("users.services.send_mail")
    def test_signup_can_return_otp_with_debug_header(self, mock_send_mail):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                f"{reverse('signup')}?debug_otp=true",
                {"email": "debug@example.com", "password": "StrongPassword123!", "role": "Seeker"},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("otp", response.data)
        self.assertRegex(response.data["otp"], r"^\d{6}$")

    @patch("users.services.send_mail")
    def test_resend_can_return_otp_with_debug_header(self, mock_send_mail):
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(
                reverse("signup"),
                {"email": "debug@example.com", "password": "StrongPassword123!", "role": "Seeker"},
                format="json",
            )

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                f"{reverse('resend-otp')}?debug_otp=true",
                {"email": "debug@example.com"},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("otp", response.data)
        self.assertRegex(response.data["otp"], r"^\d{6}$")
