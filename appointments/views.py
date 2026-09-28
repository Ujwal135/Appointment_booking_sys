from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import (
    AppointmentBookingForm,
    DoctorCreationForm,
    RegistrationForm,
    StaffAppointmentBookingForm,
)
from .models import Appointment, Doctor

User = get_user_model()


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Email or password was not recognized.')
    return render(request, 'appointments/login.html')


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account is ready. Sign in to continue.')
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'appointments/register.html', {'form': form})


@login_required
def dashboard(request):
    upcoming_appointments = Appointment.objects.filter(
        patient=request.user,
        appointment_date__gte=timezone.localdate(),
        status=Appointment.Status.SCHEDULED,
    ).select_related('doctor__user')[:3]
    return render(request, 'appointments/dashboard.html', {
        'upcoming_appointments': upcoming_appointments,
        'doctor_count': Doctor.objects.filter(is_accepting_appointments=True).count(),
    })


@login_required
def book_appointment(request):
    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.save()
            messages.success(request, 'Your appointment has been booked.')
            return redirect('appointment-history')
    else:
        form = AppointmentBookingForm()
    return render(request, 'appointments/appointment_booking.html', {'form': form})


@login_required
def appointment_history(request):
    appointments = Appointment.objects.filter(patient=request.user).select_related('doctor__user')
    return render(request, 'appointments/appointment_history.html', {'appointments': appointments})


@login_required
def doctors(request):
    doctor_list = Doctor.objects.filter(is_accepting_appointments=True).select_related('user')
    return render(request, 'appointments/doctors.html', {'doctors': doctor_list})


@login_required
def cancel_appointment(request, appointment_id):
    if request.method == 'POST':
        appointment = Appointment.objects.filter(
            pk=appointment_id,
            patient=request.user,
            status=Appointment.Status.SCHEDULED,
        ).first()
        if appointment:
            appointment.status = Appointment.Status.CANCELLED
            appointment.save(update_fields=['status'])
            messages.success(request, 'Appointment cancelled.')
    return redirect('appointment-history')


def logout_view(request):
    if request.method == 'POST':
        auth_logout(request)
    return redirect('login')


staff_required = user_passes_test(lambda user: user.is_staff)


@staff_required
def staff_manage(request):
    doctors = Doctor.objects.select_related('user')
    patients = User.objects.filter(
        is_active=True,
        is_staff=False,
        is_superuser=False,
        doctor_profile__isnull=True,
    ).order_by('last_name', 'first_name')
    return render(request, 'appointments/staff_manage.html', {
        'doctors': doctors,
        'patients': patients,
    })


@staff_required
def staff_add_doctor(request):
    form = DoctorCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Doctor added to the care team.')
        return redirect('staff-manage')
    return render(request, 'appointments/staff_form.html', {
        'form': form,
        'title': 'Add a doctor',
        'description': 'Create a doctor account and add their care profile.',
        'submit_label': 'Add doctor',
    })


@staff_required
def staff_add_patient(request):
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Patient account created.')
        return redirect('staff-manage')
    return render(request, 'appointments/staff_form.html', {
        'form': form,
        'title': 'Add a patient',
        'description': 'Create a patient account for appointment booking.',
        'submit_label': 'Add patient',
    })


@staff_required
def staff_book_appointment(request):
    initial = {'patient': request.GET.get('patient')} if request.method == 'GET' else None
    form = StaffAppointmentBookingForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Appointment booked for the selected patient.')
        return redirect('staff-manage')
    return render(request, 'appointments/staff_booking.html', {'form': form})