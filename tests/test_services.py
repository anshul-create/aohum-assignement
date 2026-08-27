from unittest.mock import patch

from django.utils import timezone
from django.test import TransactionTestCase, override_settings

from users.models import UserProfile, EmailOTP
from users.services import create_user, verify_otp, resend_otp


@override_settings(OTP_TTL_MINUTES=10, DEFAULT_FROM_EMAIL="noreply@ahoum.local")
class OTPResendSemanticsTests(TransactionTestCase):

    @patch("users.services.send_mail")
    def test_resend_invalidates_otp1_and_accepts_otp2(self, mock_send_mail):
        # 1. Create user (Generates OTP1)
        create_user(
            email="test@example.com",
            password="StrongPassword123!",
            role=UserProfile.Role.SEEKER,
        )
        otp1_code = mock_send_mail.call_args.kwargs["message"].split(": ")[1]

        # 2. Resend OTP (Generates OTP2)
        resend_otp(email="test@example.com")
        otp2_code = mock_send_mail.call_args.kwargs["message"].split(": ")[1]

        # 3. Assert OTP1 is rejected
        with self.assertRaises(ValueError) as ctx:
            verify_otp(email="test@example.com", otp_code=otp1_code)
        self.assertIn("Invalid OTP code", str(ctx.exception))

        # 4. Assert OTP2 is accepted
        self.assertTrue(verify_otp(email="test@example.com", otp_code=otp2_code))

    @patch("users.services.send_mail")
    def test_resend_fails_for_already_verified_user(self, mock_send_mail):
        create_user(
            email="test@example.com",
            password="StrongPassword123!",
            role=UserProfile.Role.SEEKER,
        )
        otp_code = mock_send_mail.call_args.kwargs["message"].split(": ")[1]
        verify_otp(email="test@example.com", otp_code=otp_code)

        with self.assertRaises(ValueError) as ctx:
            resend_otp(email="test@example.com")
        self.assertIn("already verified", str(ctx.exception))

    @patch("users.services.send_mail")
    def test_verify_otp_rejects_expired_code(self, mock_send_mail):
        create_user(
            email="test@example.com",
            password="StrongPassword123!",
            role=UserProfile.Role.SEEKER,
        )

        otp_code = mock_send_mail.call_args.kwargs["message"].split(": ")[1]
        otp_record = EmailOTP.objects.get(user__email="test@example.com")
        otp_record.expires_at = timezone.now() - timezone.timedelta(seconds=1)
        otp_record.save(update_fields=["expires_at"])

        with self.assertRaises(ValueError) as ctx:
            verify_otp(email="test@example.com", otp_code=otp_code)

        self.assertIn("expired", str(ctx.exception))
        otp_record.refresh_from_db()
        self.assertEqual(otp_record.attempts, 0)

    @patch("users.services.send_mail")
    def test_verify_otp_locks_after_three_failed_attempts(self, mock_send_mail):
        create_user(
            email="test@example.com",
            password="StrongPassword123!",
            role=UserProfile.Role.SEEKER,
        )

        for expected_attempts in (1, 2, 3):
            with self.assertRaises(ValueError) as ctx:
                verify_otp(email="test@example.com", otp_code="000000")

            self.assertIn("Invalid OTP code", str(ctx.exception))
            otp_record = EmailOTP.objects.get(user__email="test@example.com")
            self.assertEqual(otp_record.attempts, expected_attempts)

        with self.assertRaises(ValueError) as ctx:
            verify_otp(email="test@example.com", otp_code="000000")

        self.assertIn("Too many failed attempts", str(ctx.exception))
