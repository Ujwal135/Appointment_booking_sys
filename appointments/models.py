from django.conf import settings
from django.db import models
from django.db.models import Q


class Doctor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_profile',
    )
    specialty = models.CharField(max_length=120)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    is_accepting_appointments = models.BooleanField(default=True)

    class Meta:
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return f'Dr. {self.user.get_full_name() or self.user.username}'


class Appointment(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments',
    )
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, related_name='appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.SCHEDULED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['appointment_date', 'appointment_time']
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'appointment_date', 'appointment_time'],
                condition=~Q(status='cancelled'),
                name='unique_active_doctor_appointment_slot',
            ),
        ]

    def __str__(self):
        return f'{self.patient} with {self.doctor} on {self.appointment_date}'