from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone

from .models import Appointment, Doctor

User = get_user_model()


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'email')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = user.email
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class DoctorCreationForm(forms.Form):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    specialty = forms.CharField(max_length=120)
    phone = forms.CharField(max_length=30, required=False)
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_password(self):
        password = self.cleaned_data['password']
        user = User(
            username=self.data.get('email', '').strip().lower(),
            first_name=self.data.get('first_name', ''),
            last_name=self.data.get('last_name', ''),
            email=self.data.get('email', ''),
        )
        validate_password(password, user=user)
        return password

    @transaction.atomic
    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data['email'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
        )
        return Doctor.objects.create(
            user=user,
            specialty=self.cleaned_data['specialty'],
            phone=self.cleaned_data['phone'],
            bio=self.cleaned_data['bio'],
        )


class AppointmentBookingForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ('doctor', 'appointment_date', 'appointment_time', 'reason')
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date'}),
            'appointment_time': forms.TimeInput(attrs={'type': 'time'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['doctor'].queryset = Doctor.objects.filter(is_accepting_appointments=True)

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')
        if appointment_date and appointment_date < timezone.localdate():
            self.add_error('appointment_date', 'Choose today or a future date.')
        if doctor and appointment_date and appointment_time:
            conflict = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
            ).exclude(status=Appointment.Status.CANCELLED)
            if self.instance.pk:
                conflict = conflict.exclude(pk=self.instance.pk)
            if conflict.exists():
                raise forms.ValidationError('That time is already booked. Please choose another slot.')
        return cleaned_data


class StaffAppointmentBookingForm(AppointmentBookingForm):
    class Meta(AppointmentBookingForm.Meta):
        fields = ('patient', 'doctor', 'appointment_date', 'appointment_time', 'reason')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['patient'].queryset = User.objects.filter(
            is_active=True,
            is_staff=False,
            is_superuser=False,
            doctor_profile__isnull=True,
        ).order_by('last_name', 'first_name', 'email')