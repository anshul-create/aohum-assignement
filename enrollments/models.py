# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from events.models import Event

class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('canceled', 'Canceled'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='enrollments')
    seeker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Only one active (non-canceled) enrollment per (event, seeker)
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'seeker'],
                condition=models.Q(status='enrolled'),
                name='unique_active_enrollment'
            )
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.seeker.email} - {self.event.title} ({self.status})"

    def clean(self):
        if self.status == 'enrolled' and self.event.is_full():
            raise ValidationError("Event is at full capacity.")