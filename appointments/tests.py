from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .forms import AppointmentBookingForm
from .models import Appointment, Doctor

User = get_user_model()


class AppointmentFlowTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            username='patient@example.com',
            email='patient@example.com',
            password='Safe-password-123',
        )
        self.staff = User.objects.create_user(
            username='staff@example.com',
            email='staff@example.com',
            password='Safe-password-123',
            is_staff=True,
        )
        doctor_user = User.objects.create_user(
            username='doctor@example.com',
            email='doctor@example.com',
            first_name='Ada',
            last_name='Lovelace',
            password='Safe-password-123',
        )
        self.doctor = Doctor.objects.create(user=doctor_user, specialty='Cardiology')

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, f'{reverse("login")}?next={reverse("dashboard")}')

    def test_patient_can_see_doctor_list(self):
        self.client.force_login(self.patient)
        response = self.client.get(reverse('doctors'))
        self.assertContains(response, 'Cardiology')

    def test_appointment_history_is_limited_to_signed_in_patient(self):
        other_patient = User.objects.create_user(
            username='other@example.com',
            email='other@example.com',
            password='Safe-password-123',
        )
        Appointment.objects.create(
            patient=other_patient,
            doctor=self.doctor,
            appointment_date='2030-06-01',
            appointment_time='10:00',
        )
        self.client.force_login(self.patient)
        response = self.client.get(reverse('appointment-history'))
        self.assertEqual(response.context['appointments'].count(), 0)

    def test_booked_doctor_time_cannot_be_selected_twice(self):
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date='2030-06-01',
            appointment_time='10:00',
        )
        form = AppointmentBookingForm(data={
            'doctor': self.doctor.pk,
            'appointment_date': '2030-06-01',
            'appointment_time': '10:00',
            'reason': 'Annual checkup',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('already booked', str(form.errors))

    def test_patient_can_register_with_email_and_password(self):
        response = self.client.post(reverse('register'), {
            'first_name': 'Grace',
            'last_name': 'Hopper',
            'email': 'grace@example.com',
            'password1': 'Good-password-456',
            'password2': 'Good-password-456',
        })
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(username='grace@example.com').exists())

    def test_patient_cannot_cancel_another_patients_appointment(self):
        other_patient = User.objects.create_user(
            username='other@example.com',
            email='other@example.com',
            password='Safe-password-123',
        )
        appointment = Appointment.objects.create(
            patient=other_patient,
            doctor=self.doctor,
            appointment_date='2030-06-01',
            appointment_time='10:00',
        )
        self.client.force_login(self.patient)
        self.client.post(reverse('appointment-cancel', args=[appointment.pk]))
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.SCHEDULED)

    def test_api_patient_appointments_are_private_and_include_doctor_name(self):
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date='2030-06-01',
            appointment_time='10:00',
        )
        other_patient = User.objects.create_user(
            username='other@example.com',
            email='other@example.com',
            password='Safe-password-123',
        )
        Appointment.objects.create(
            patient=other_patient,
            doctor=self.doctor,
            appointment_date='2030-06-01',
            appointment_time='11:00',
        )
        api_client = APIClient()
        api_client.force_authenticate(user=self.patient)
        response = api_client.get('/api/appointments/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['doctor_name'], 'Dr. Ada Lovelace')

    def test_api_rejects_an_occupied_time_slot(self):
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date='2030-06-01',
            appointment_time='10:00',
        )
        api_client = APIClient()
        api_client.force_authenticate(user=self.patient)
        response = api_client.post('/api/appointments/', {
            'doctor': self.doctor.pk,
            'appointment_date': '2030-06-01',
            'appointment_time': '10:00',
            'reason': 'Follow-up',
        })
        self.assertEqual(response.status_code, 400)

    def test_staff_tools_are_not_available_to_patients(self):
        self.client.force_login(self.patient)
        response = self.client.get(reverse('staff-manage'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_staff_pages_render_for_staff(self):
        self.client.force_login(self.staff)
        staff_pages = (
            ('staff-manage', 'Staff tools'),
            ('staff-add-doctor', 'Add a doctor'),
            ('staff-add-patient', 'Add a patient'),
            ('staff-book-appointment', 'Book for a patient'),
        )
        for route_name, heading in staff_pages:
            with self.subTest(route=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, heading)

    def test_staff_directory_shortcut_preselects_patient(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('staff-book-appointment'), {'patient': self.patient.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form']['patient'].value(), str(self.patient.pk))

    def test_staff_can_add_a_doctor(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse('staff-add-doctor'), {
            'first_name': 'Katherine',
            'last_name': 'Johnson',
            'email': 'katherine@example.com',
            'password': 'Doctor!Pass8472',
            'specialty': 'Pediatrics',
            'phone': '555-0199',
            'bio': 'Pediatric care',
        })
        self.assertRedirects(response, reverse('staff-manage'))
        self.assertTrue(Doctor.objects.filter(user__email='katherine@example.com', specialty='Pediatrics').exists())

    def test_staff_can_add_a_patient(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse('staff-add-patient'), {
            'first_name': 'Katherine',
            'last_name': 'Johnson',
            'email': 'katherine.patient@example.com',
            'password1': 'Patient!Pass8472',
            'password2': 'Patient!Pass8472',
        })
        self.assertRedirects(response, reverse('staff-manage'))
        self.assertTrue(User.objects.filter(email='katherine.patient@example.com').exists())

    def test_staff_can_book_for_selected_patient(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse('staff-book-appointment'), {
            'patient': self.patient.pk,
            'doctor': self.doctor.pk,
            'appointment_date': '2030-06-01',
            'appointment_time': '10:00',
            'reason': 'Annual checkup',
        })
        self.assertRedirects(response, reverse('staff-manage'))
        appointment = Appointment.objects.get(appointment_date='2030-06-01')
        self.assertEqual(appointment.patient, self.patient)
        self.assertEqual(appointment.doctor, self.doctor)