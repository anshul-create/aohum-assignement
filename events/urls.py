from django.urls import path
from .views import EventListCreateView, EventDetailView, MyEventsView

urlpatterns = [
    path('', EventListCreateView.as_view(), name='event-list'),
    path('<int:pk>/', EventDetailView.as_view(), name='event-detail'),
    path('my-events/', MyEventsView.as_view(), name='my-events'),
]