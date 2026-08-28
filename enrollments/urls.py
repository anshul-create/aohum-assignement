from django.urls import path
from .views import EnrollView, CancelEnrollmentView, MyEnrollmentsView

urlpatterns = [
    path('', EnrollView.as_view(), name='enroll'),
    path('<int:pk>/cancel/', CancelEnrollmentView.as_view(), name='cancel-enrollment'),
    path('my-enrollments/', MyEnrollmentsView.as_view(), name='my-enrollments'),
]