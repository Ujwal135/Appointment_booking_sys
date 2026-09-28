from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Appointment, Doctor
from .serializers import AppointmentSerializer, DoctorSerializer, RegistrationSerializer


class RegistrationAPIView(generics.CreateAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]


class DoctorListAPIView(generics.ListAPIView):
    serializer_class = DoctorSerializer
    permission_classes = [AllowAny]
    queryset = Doctor.objects.filter(is_accepting_appointments=True).select_related('user')


class AppointmentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Appointment.objects.filter(patient=self.request.user).select_related('doctor__user')

    def perform_create(self, serializer):
        serializer.save(patient=self.request.user)