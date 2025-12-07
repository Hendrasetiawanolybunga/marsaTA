from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    # Homepage
    path('', views.home, name='home'),
    
    # Authentication paths
    path('registrasi/', views.registrasi_pasien, name='registrasi_pasien'),
    path('login/', views.login_pasien, name='login_pasien'),
    path('logout/', views.logout_pasien, name='logout_pasien'),
    path('dashboard/', views.dashboard_pasien, name='dashboard_pasien'),
    path('akun/edit/', views.edit_akun_pasien, name='edit_akun_pasien'),
    
    # Anthropometric measurement paths
    path('pengukuran/input/', views.input_pengukuran, name='input_pengukuran'),
    
    # Paths for diagnosis
    path('diagnosa/', views.form_diagnosa, name='form_diagnosa'),
    path('diagnosa/hasil/<int:konsultasi_id>/', views.tampilkan_hasil_diagnosa, name='tampilkan_hasil_diagnosa'),
    
    # Paths for anthropometric data and notifications
    path('grafik/<int:pasien_id>/', views.tampilkan_grafik_riwayat, name='tampilkan_grafik_riwayat'),
    
    # Expert/Admin paths
    path('pakar/rules/create/', views.create_rule_group, name='create_rule_group'),
    path('pakar/patients/', views.list_patients_pakar, name='list_patients_pakar'),
    path('pakar/patients/<int:pasien_id>/', views.detail_pasien_pakar, name='detail_pasien_pakar'),
    path('pakar/rules/', views.list_rules_pakar, name='list_rules_pakar'),
]