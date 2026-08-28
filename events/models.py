from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    language = models.CharField(max_length=50)
    location = models.CharField(max_length=200)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    capacity = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['starts_at']),
            models.Index(fields=['location']),
            models.Index(fields=['language']),
        ]
        ordering = ['starts_at']   # upcoming first by default

    def __str__(self):
        return self.title

    def active_enrollments_count(self):
        """Count of currently enrolled participants."""
        # `enrollments` comes from the Enrollment model (enrollments app).
        # Guard until that app exists so event listing/creation does not 500.
        related = getattr(self, "enrollments", None)
        if related is None:
            return 0
        return related.filter(status='enrolled').count()

    def is_full(self):
        if self.capacity is None:
            return False
        return self.active_enrollments_count() >= self.capacity

    def available_spots(self):
        if self.capacity is None:
            return None
        return max(0, self.capacity - self.active_enrollments_count())

    def active_enrollments_count(self):
        return self.enrollments.filter(status='enrolled').count()

    def has_available_spots(self):
        if self.capacity is None:
            return True
        return self.active_enrollments_count() < self.capacity

    def is_full(self):
        if self.capacity is None:
            return False
        return self.active_enrollments_count() >= self.capacity