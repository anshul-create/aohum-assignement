from rest_framework import permissions
from users.models import UserProfile

class IsFacilitator(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            return request.user.profile.role == 'Facilitator'
        except UserProfile.DoesNotExist:
            return False

class IsEventCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user