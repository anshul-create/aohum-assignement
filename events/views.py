from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from django.utils import timezone
from .models import Event
from .serializers import EventSerializer
from .permissions import IsFacilitator, IsEventCreator

class EventListCreateView(generics.ListCreateAPIView):
    """
    GET: List all upcoming events with search/filter (public)
    POST: Create a new event (Facilitator only)
    """
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        # Base: only upcoming events
        queryset = Event.objects.filter(starts_at__gte=timezone.now())

        # Search by title or description
        q = self.request.query_params.get('q')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) | Q(description__icontains=q)
            )

        # Filter by location (case‑insensitive partial match)
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)

        # Filter by language
        language = self.request.query_params.get('language')
        if language:
            queryset = queryset.filter(language__icontains=language)

        # Date range filters
        starts_after = self.request.query_params.get('starts_after')
        if starts_after:
            queryset = queryset.filter(starts_at__gte=starts_after)

        starts_before = self.request.query_params.get('starts_before')
        if starts_before:
            queryset = queryset.filter(starts_at__lte=starts_before)

        # Default ordering: upcoming first (already applied in Meta)
        return queryset

    def perform_create(self, serializer):
        # Only facilitators can create events
        if not self.request.user.profile.role == 'Facilitator':
            raise PermissionDenied(
                {"detail": "Only facilitators can create events.", "code": "not_facilitator"}
            )
        serializer.save(created_by=self.request.user)

class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific event.
    - GET: any authenticated user (or even public, but we keep auth for consistency)
    - PUT/PATCH: only the creator (Facilitator)
    - DELETE: only the creator (Facilitator)
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsEventCreator]

    def perform_update(self, serializer):
        # Check that user is facilitator (double‑check)
        if self.request.user.profile.role != 'Facilitator':
            raise PermissionDenied(
                {"detail": "Only facilitators can update events.", "code": "not_facilitator"}
            )
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user.profile.role != 'Facilitator':
            raise PermissionDenied(
                {"detail": "Only facilitators can delete events.", "code": "not_facilitator"}
            )
        instance.delete()

class MyEventsView(generics.ListAPIView):
    """
    List events created by the authenticated facilitator.
    Includes enrollment counts and available spots.
    """
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated, IsFacilitator]

    def get_queryset(self):
        return Event.objects.filter(created_by=self.request.user).order_by('starts_at')