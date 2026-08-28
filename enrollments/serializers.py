from rest_framework import serializers
from .models import Enrollment
from events.serializers import EventSerializer

class EnrollmentSerializer(serializers.ModelSerializer):
    event_detail = EventSerializer(source='event', read_only=True)
    seeker_email = serializers.EmailField(source='seeker.email', read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            'id', 'event', 'event_detail', 'seeker', 'seeker_email',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['seeker', 'created_at', 'updated_at']