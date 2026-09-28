from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('appointments/book/', views.book_appointment, name='appointment-booking'),
    path('appointments/history/', views.appointment_history, name='appointment-history'),
    path('appointments/<int:appointment_id>/cancel/', views.cancel_appointment, name='appointment-cancel'),
    path('doctors/', views.doctors, name='doctors'),
    path('staff/', views.staff_manage, name='staff-manage'),
    path('staff/doctors/add/', views.staff_add_doctor, name='staff-add-doctor'),
    path('staff/patients/add/', views.staff_add_patient, name='staff-add-patient'),
    path('staff/appointments/book/', views.staff_book_appointment, name='staff-book-appointment'),
    path('api/', include('appointments.api_urls')),
]