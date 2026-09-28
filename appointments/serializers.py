from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from .models import Appointment, Doctor

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password')

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return email

    def create(self, validated_data):
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        return User.objects.create_user(username=email, email=email, password=password, **validated_data)


class DoctorSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = Doctor
        fields = ('id', 'name', 'specialty', 'bio', 'phone')


class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    patient = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Appointment
        fields = (
            'id', 'patient', 'doctor', 'doctor_name', 'appointment_date',
            'appointment_time', 'reason', 'status', 'created_at',
        )
        read_only_fields = ('id', 'status', 'created_at')

    def validate(self, attrs):
        doctor = attrs['doctor']
        appointment_date = attrs['appointment_date']
        appointment_time = attrs['appointment_time']
        if not doctor.is_accepting_appointments:
            raise serializers.ValidationError({'doctor': 'This doctor is not accepting appointments.'})
        if appointment_date < timezone.localdate():
            raise serializers.ValidationError({'appointment_date': 'Choose today or a future date.'})
        conflict = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
        ).exclude(status=Appointment.Status.CANCELLED)
        if conflict.exists():
            raise serializers.ValidationError({'appointment_time': 'That time is already booked.'})
        return attrs

    def get_doctor_name(self, appointment):
        return str(appointment.doctor)