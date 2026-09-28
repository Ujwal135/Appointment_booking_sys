from django.contrib import admin

from .models import Appointment, Doctor


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialty', 'is_accepting_appointments')
    list_filter = ('specialty', 'is_accepting_appointments')
    search_fields = ('user__first_name', 'user__last_name', 'specialty')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'appointment_date', 'appointment_time', 'status')
    list_filter = ('status', 'appointment_date')
    search_fields = ('patient__username', 'doctor__user__last_name')