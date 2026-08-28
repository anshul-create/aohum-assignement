from django.shortcuts import render

# Create your views here.
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from .models import Enrollment
from .serializers import EnrollmentSerializer
from events.models import Event

class EnrollView(generics.CreateAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        if user.profile.role != 'Seeker':
            raise PermissionDenied(
                {"detail": "Only seekers can enroll.", "code": "not_seeker"}
            )

        event_id = self.request.data.get('event')
        if not event_id:
            raise ValidationError({"detail": "Event ID required.", "code": "missing_event"})

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            raise ValidationError({"detail": "Event not found.", "code": "event_not_found"})

        if event.starts_at < timezone.now():
            raise ValidationError(
                {"detail": "Cannot enroll in past event.", "code": "past_event"}
            )

        # Concurrency-safe enrollment with select_for_update
        with transaction.atomic():
            event = Event.objects.select_for_update().get(id=event_id)
            existing = Enrollment.objects.filter(event=event, seeker=user).first()

            if existing:
                if existing.status == 'enrolled':
                    raise ValidationError(
                        {"detail": "Already enrolled.", "code": "already_enrolled"}
                    )
                elif existing.status == 'canceled':
                    # RE-ENROLL: check capacity, then reactivate
                    if event.is_full():
                        raise ValidationError(
                            {"detail": "Event full.", "code": "event_full"}
                        )
                    existing.status = 'enrolled'
                    existing.save()
                    serializer.instance = existing
                    return
            else:
                # New enrollment – check capacity
                if event.is_full():
                    raise ValidationError(
                        {"detail": "Event full.", "code": "event_full"}
                    )

            serializer.save(event=event, seeker=user)


class CancelEnrollmentView(generics.DestroyAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(seeker=self.request.user)

    def perform_destroy(self, instance):
        if instance.status == 'canceled':
            raise ValidationError(
                {"detail": "Already canceled.", "code": "already_canceled"}
            )
        instance.status = 'canceled'
        instance.save()


class MyEnrollmentsView(generics.ListAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Enrollment.objects.filter(seeker=self.request.user)

        status_filter = self.request.query_params.get('status')
        if status_filter in ['enrolled', 'canceled']:
            queryset = queryset.filter(status=status_filter)

        time_filter = self.request.query_params.get('time')
        now = timezone.now()
        if time_filter == 'upcoming':
            queryset = queryset.filter(event__starts_at__gte=now)
        elif time_filter == 'past':
            queryset = queryset.filter(event__starts_at__lt=now)

        return queryset.order_by('event__starts_at')