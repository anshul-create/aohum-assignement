from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from events.models import Event
from users.models import UserProfile


class EventDetailTests(APITestCase):
    def setUp(self):
        self.facilitator = User.objects.create_user(
            username='facilitator@test.com',
            email='facilitator@test.com',
            password='pass',
        )
        UserProfile.objects.create(
            user=self.facilitator,
            role='Facilitator',
            email_verified=True,
        )
        self.event = Event.objects.create(
            title='Public Event',
            description='Desc',
            language='English',
            location='Online',
            starts_at=timezone.now() + timezone.timedelta(days=1),
            ends_at=timezone.now() + timezone.timedelta(days=1, hours=2),
            capacity=10,
            created_by=self.facilitator,
        )
        self.detail_url = reverse('event-detail', args=[self.event.id])

    def test_event_detail_is_public_without_bearer_token(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.event.id)
