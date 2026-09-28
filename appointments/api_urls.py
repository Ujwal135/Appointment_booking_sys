from django.urls import path

from .api_views import AppointmentListCreateAPIView, DoctorListAPIView, RegistrationAPIView

urlpatterns = [
    path('register/', RegistrationAPIView.as_view(), name='api-register'),
    path('doctors/', DoctorListAPIView.as_view(), name='api-doctors'),
    path('appointments/', AppointmentListCreateAPIView.as_view(), name='api-appointments'),
]