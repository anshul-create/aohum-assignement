from django.utils import timezone
from rest_framework import serializers
from .models import Event

class EventSerializer(serializers.ModelSerializer):
    enrolled_count = serializers.SerializerMethodField()
    available_spots = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'language', 'location',
            'starts_at', 'ends_at', 'capacity',
            'enrolled_count', 'available_spots', 'is_full',
            'created_by', 'created_by_email', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def get_enrolled_count(self, obj):
        return obj.active_enrollments_count()

    def get_available_spots(self, obj):
        return obj.available_spots()

    def get_is_full(self, obj):
        return obj.is_full()

    def validate(self, data):
        starts_at = data.get('starts_at')
        ends_at = data.get('ends_at')
        if starts_at and ends_at:
            if starts_at >= ends_at:
                raise serializers.ValidationError({
                    'detail': 'End time must be after start time.',
                    'code': 'invalid_time_range'
                })
            if starts_at < timezone.now():
                raise serializers.ValidationError({
                    'detail': 'Event cannot start in the past.',
                    'code': 'past_start_time'
                })
        return data