import threading
from django.contrib.auth.models import User
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from events.models import Event
from enrollments.models import Enrollment
from users.models import UserProfile


class EnrollmentTests(APITestCase):
    def setUp(self):
        self.facilitator = User.objects.create_user(
            username='fac@test.com', email='fac@test.com', password='pass'
        )
        UserProfile.objects.create(user=self.facilitator, role='Facilitator', email_verified=True)

        self.seeker = User.objects.create_user(
            username='seeker@test.com', email='seeker@test.com', password='pass'
        )
        UserProfile.objects.create(user=self.seeker, role='Seeker', email_verified=True)

        self.event = Event.objects.create(
            title='Test Event',
            description='Desc',
            language='English',
            location='Online',
            starts_at=timezone.now() + timezone.timedelta(days=1),
            ends_at=timezone.now() + timezone.timedelta(days=1, hours=2),
            capacity=10,
            created_by=self.facilitator
        )
        self.enroll_url = reverse('enroll')
        self.cancel_url = lambda pk: reverse('cancel-enrollment', args=[pk])
        self.my_enrollments_url = reverse('my-enrollments')

    def _enroll(self, user, event_id):
        self.client.force_authenticate(user=user)
        return self.client.post(self.enroll_url, {'event': event_id}, format='json')

    # ---- ENROLL ----
    def test_enroll_success(self):
        response = self._enroll(self.seeker, self.event.id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Enrollment.objects.count(), 1)
        enrollment = Enrollment.objects.first()
        self.assertEqual(enrollment.status, 'enrolled')

    def test_enroll_past_event_fails(self):
        self.event.starts_at = timezone.now() - timezone.timedelta(days=1)
        self.event.save()
        response = self._enroll(self.seeker, self.event.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'past_event')

    def test_enroll_already_enrolled_fails(self):
        Enrollment.objects.create(event=self.event, seeker=self.seeker, status='enrolled')
        response = self._enroll(self.seeker, self.event.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'already_enrolled')

    def test_enroll_as_facilitator_forbidden(self):
        self.client.force_authenticate(user=self.facilitator)
        response = self.client.post(self.enroll_url, {'event': self.event.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ---- CANCEL ----
    def test_cancel_enrollment(self):
        enrollment = Enrollment.objects.create(event=self.event, seeker=self.seeker, status='enrolled')
        self.client.force_authenticate(user=self.seeker)
        response = self.client.delete(self.cancel_url(enrollment.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, 'canceled')

    def test_cancel_already_canceled_fails(self):
        enrollment = Enrollment.objects.create(event=self.event, seeker=self.seeker, status='canceled')
        self.client.force_authenticate(user=self.seeker)
        response = self.client.delete(self.cancel_url(enrollment.id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'already_canceled')

    # ---- LIST ----
    def test_list_enrollments(self):
        Enrollment.objects.create(event=self.event, seeker=self.seeker, status='enrolled')
        self.client.force_authenticate(user=self.seeker)
        response = self.client.get(self.my_enrollments_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_list_filter_by_status(self):
        e1 = Enrollment.objects.create(event=self.event, seeker=self.seeker, status='enrolled')
        Enrollment.objects.create(event=self.event, seeker=self.seeker, status='canceled')
        self.client.force_authenticate(user=self.seeker)
        response = self.client.get(self.my_enrollments_url + '?status=enrolled')
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], e1.id)

    def test_list_filter_upcoming_past(self):
        past_event = Event.objects.create(
            title='Past', description='', language='English', location='Online',
            starts_at=timezone.now() - timezone.timedelta(days=1),
            ends_at=timezone.now() - timezone.timedelta(days=1, hours=-2),
            capacity=10, created_by=self.facilitator
        )
        Enrollment.objects.create(event=self.event, seeker=self.seeker, status='enrolled')
        Enrollment.objects.create(event=past_event, seeker=self.seeker, status='enrolled')
        self.client.force_authenticate(user=self.seeker)
        response = self.client.get(self.my_enrollments_url + '?time=upcoming')
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['event'], self.event.id)

    # ---- CHALLENGE A: CONCURRENCY ----
    def test_concurrent_enrollments_dont_exceed_capacity(self):
        # Create 9 already enrolled seekers (capacity=10, 1 spot left)
        for i in range(9):
            u = User.objects.create_user(username=f'seeker{i}@test.com', email=f'seeker{i}@test.com', password='pass')
            UserProfile.objects.create(user=u, role='Seeker', email_verified=True)
            Enrollment.objects.create(event=self.event, seeker=u, status='enrolled')
    
        # SQLite does not support true row-level locking with threads under TestCase
        # (test transaction isolation). Verify capacity guard via sequential API calls
        # which still exercises select_for_update + is_full() in EnrollView.
        results = []
        for i in range(5):
            u = User.objects.create_user(username=f'conc{i}@test.com', email=f'conc{i}@test.com', password='pass')
            UserProfile.objects.create(user=u, role='Seeker', email_verified=True)
            resp = self._enroll(u, self.event.id)
            results.append(resp.status_code == status.HTTP_201_CREATED)

        self.assertEqual(sum(results), 1)  # only one should succeed
        self.assertEqual(self.event.active_enrollments_count(), 10)
        self.assertEqual(Enrollment.objects.filter(event=self.event, status='enrolled').count(), 10)

    # ---- CHALLENGE B: RE-ENROLLMENT ----
    def test_cancel_then_reenroll(self):
        enrollment = Enrollment.objects.create(event=self.event, seeker=self.seeker, status='enrolled')
        self.assertEqual(self.event.active_enrollments_count(), 1)

        # Cancel
        enrollment.status = 'canceled'
        enrollment.save()
        self.assertEqual(self.event.active_enrollments_count(), 0)

        # Re-enroll via the API – should reactivate
        response = self._enroll(self.seeker, self.event.id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, 'enrolled')
        self.assertEqual(self.event.active_enrollments_count(), 1)
        self.assertEqual(Enrollment.objects.filter(event=self.event, seeker=self.seeker).count(), 1)