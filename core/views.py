from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Pasien, Konsultasi, DetailKonsultasi, Gejala, Kondisi, Aturan, PengukuranFisik, Notifikasi
from django.db.models import Count
from collections import defaultdict
import random
from datetime import date, timedelta
from .utils import hitung_dan_simpan_zscore, buat_jadwal_notifikasi
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms import modelformset_factory, ModelForm
from django import forms

# Helper function to check if user is staff
def is_staff(user):
    return user.is_staff

# Index view - redirect authenticated users to appropriate dashboard
def home(request):
    # If user is staff, redirect to expert dashboard
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('list_patients_pakar')
    
    # If patient is logged in, redirect to patient dashboard
    if 'pasien_id' in request.session:
        return redirect('dashboard_pasien')
    
    # Otherwise, show the home page
    return render(request, 'index.html')

# Create your views here.

# PROMPT #1: Mesin Inferensi Forward Chaining Inti
def jalankan_inferensi(pasien_id, kode_gejala_input):
    """
    Implementasi Mesin Inferensi menggunakan metode Forward Chaining (Rantai Maju)
    
    Args:
        pasien_id: ID dari objek Pasien
        kode_gejala_input: List berisi kode-kode gejala (misal: ['G01', 'G04', 'G10'])
        
    Returns:
        Objek Konsultasi yang berisi hasil diagnosa
    """
    
    # Langkah 1: Inisiasi dan Pencatatan Konsultasi
    try:
        pasien = Pasien.objects.get(id=pasien_id)
    except Pasien.DoesNotExist:
        raise ValueError("Pasien tidak ditemukan")
    
    # Buat objek Konsultasi baru
    konsultasi = Konsultasi.objects.create(pasien=pasien)
    
    # Catat semua kode_gejala_input ke dalam DetailKonsultasi
    for kode_gejala in kode_gejala_input:
        try:
            gejala = Gejala.objects.get(kodeGejala=kode_gejala)
            DetailKonsultasi.objects.create(konsultasi=konsultasi, gejala=gejala)
        except Gejala.DoesNotExist:
            # Lewati gejala yang tidak ditemukan
            continue
    
    # Inisialisasi Working Memory (WM) dengan kode_gejala_input
    working_memory = set(kode_gejala_input)
    
    # Langkah 2: Logika Forward Chaining (Pencocokan Aturan AND)
    # Ambil semua objek Aturan dari database
    semua_aturan = Aturan.objects.select_related('kondisi', 'gejala').all()
    
    # Kelompokkan aturan berdasarkan pasangan kondisi dan kodeKelompokAturan
    aturan_kelompok = defaultdict(list)
    for aturan in semua_aturan:
        key = (aturan.kondisi.kodeKondisi, aturan.kodeKelompokAturan)
        aturan_kelompok[key].append(aturan)
    
    # Ulangi setiap kelompok aturan yang teridentifikasi
    diagnosis_ditemukan = False
    hasil_kondisi = None
    
    for (kode_kondisi, kode_kelompok), aturan_list in aturan_kelompok.items():
        if diagnosis_ditemukan:
            break
            
        # Hitung jumlah total gejala yang dibutuhkan oleh kelompok aturan tersebut
        total_gejala_dibutuhkan = len(aturan_list)
        
        # Periksa apakah SEMUA gejala yang dibutuhkan ada dalam Working Memory saat ini
        gejala_dibutuhkan = set(aturan.gejala.kodeGejala for aturan in aturan_list)
        if gejala_dibutuhkan.issubset(working_memory):
            # Aktivasi (Firing): Jika suatu kelompok aturan terpenuhi (match 100%)
            # Ambil kodeKondisi hasil
            try:
                hasil_kondisi = Kondisi.objects.get(kodeKondisi=kode_kondisi)
                
                # Set hasilKondisi pada objek Konsultasi yang sedang berjalan
                konsultasi.hasilKondisi = hasil_kondisi
                
                # Hentikan proses looping dan forward chaining karena tujuan (diagnosis) telah tercapai
                diagnosis_ditemukan = True
                break
            except Kondisi.DoesNotExist:
                # Jika kondisi tidak ditemukan, lanjutkan ke kelompok aturan berikutnya
                continue
    
    # Output dan Penyimpanan
    # Simpan (.save()) objek Konsultasi yang sudah diisi hasilKondisi
    konsultasi.save()
    
    # Kembalikan objek Konsultasi yang berisi hasil diagnosa
    return konsultasi


# PROMPT #2: Views Django untuk Input dan Tampilan Hasil
def form_diagnosa(request):
    """
    View untuk menampilkan form diagnosa dan memproses input gejala
    """
    # Pastikan pengguna sudah login
    if 'pasien_id' not in request.session:
        return redirect('login_pasien')
    
    if request.method == 'GET':
        # Metode GET: Ambil dan tampilkan semua objek Gejala untuk ditampilkan dalam formulir HTML
        gejala_list = Gejala.objects.all()
        return render(request, 'diagnosa_form.html', {'gejala_list': gejala_list})
    
    elif request.method == 'POST':
        # Metode POST: Proses input dari form
        # Ambil kode_gejala_input (sebagai list dari nilai checkbox yang dikirimkan)
        kode_gejala_input = request.POST.getlist('gejala')
        
        # Ambil pasien_id dari sesi
        pasien_id = request.session.get('pasien_id')
        
        # Panggil fungsi jalankan_inferensi(pasien_id, kode_gejala_input)
        konsultasi = jalankan_inferensi(pasien_id, kode_gejala_input)
        
        # Redirect pengguna ke View tampilkan_hasil_diagnosa dengan ID Konsultasi yang baru dibuat
        return redirect('tampilkan_hasil_diagnosa', konsultasi_id=konsultasi.id)


def tampilkan_hasil_diagnosa(request, konsultasi_id):
    """
    View untuk menampilkan hasil diagnosa
    """
    # Pastikan pengguna sudah login
    if 'pasien_id' not in request.session:
        return redirect('login_pasien')
    
    # Ambil objek Konsultasi berdasarkan konsultasi_id
    konsultasi = Konsultasi.objects.select_related('hasilKondisi').get(id=konsultasi_id)
    
    # Ambil objek Kondisi yang menjadi hasil diagnosa
    kondisi = konsultasi.hasilKondisi
    
    # Siapkan konteks untuk template
    context = {
        'konsultasi': konsultasi,
        'kondisi': kondisi,
    }
    
    # Tampilkan namaKondisi, deskripsi, dan solusi dari hasil diagnosa tersebut
    return render(request, 'hasil_diagnosa.html', context)


# PROMPT #4: Keamanan dan Autentikasi Pasien
def registrasi_pasien(request):
    """
    View untuk menangani pendaftaran Pasien baru
    """
    if request.method == 'POST':
        # Terima data dari form
        nama_pengguna = request.POST.get('nama_pengguna')
        kata_sandi = request.POST.get('kata_sandi')
        nama = request.POST.get('nama')
        jenis_kelamin = request.POST.get('jenis_kelamin')
        tanggal_lahir = request.POST.get('tanggal_lahir')
        nama_wali = request.POST.get('nama_wali')
        nomor_telepon = request.POST.get('nomor_telepon')
        
        # Buat objek Pasien baru
        pasien = Pasien(
            namaPengguna=nama_pengguna,
            nama=nama,
            jenisKelamin=jenis_kelamin,
            tanggalLahir=tanggal_lahir,
            namaWali=nama_wali,
            nomorTelepon=nomor_telepon
        )
        
        # PENTING: Sebelum menyimpan, panggil metode set_password pada objek Pasien
        pasien.set_password(kata_sandi)
        
        # Simpan objek Pasien
        pasien.save()
        
        # Setelah registrasi sukses, redirect ke halaman login
        return redirect('login_pasien')
    
    # Metode GET: Tampilkan form registrasi
    return render(request, 'registrasi_pasien.html')


def login_pasien(request):
    """
    View untuk login Pasien
    """
    if request.method == 'POST':
        # Terima namaPengguna dan kataSandi mentah
        nama_pengguna = request.POST.get('nama_pengguna')
        kata_sandi = request.POST.get('kata_sandi')
        
        try:
            # Cari objek Pasien berdasarkan namaPengguna
            pasien = Pasien.objects.get(namaPengguna=nama_pengguna)
            
            # Gunakan metode check_password untuk memverifikasi kata sandi
            if pasien.check_password(kata_sandi):
                # Jika autentikasi sukses, buat sesi Django untuk Pasien tersebut
                request.session['pasien_id'] = pasien.id
                request.session['pasien_nama'] = pasien.nama
                
                # Redirect ke Dashboard Pasien
                return redirect('dashboard_pasien')
            else:
                # Jika password salah
                return render(request, 'login_pasien.html', {'error': 'Nama pengguna atau kata sandi salah'})
        except Pasien.DoesNotExist:
            # Jika pengguna tidak ditemukan
            return render(request, 'login_pasien.html', {'error': 'Nama pengguna atau kata sandi salah'})
    
    # Metode GET: Tampilkan form login
    return render(request, 'login_pasien.html')


def logout_pasien(request):
    """
    View untuk logout Pasien
    """
    # Hapus semua data Pasien dari sesi
    request.session.flush()
    
    # Redirect ke halaman login
    return redirect('home')


def dashboard_pasien(request):
    """
    View untuk dashboard Pasien
    """
    # Pastikan pengguna sudah login (cek pasien_id di sesi)
    if 'pasien_id' not in request.session:
        return redirect('login_pasien')
    
    # Ambil data Pasien yang sedang login
    pasien_id = request.session.get('pasien_id')
    try:
        pasien = Pasien.objects.get(id=pasien_id)
    except Pasien.DoesNotExist:
        # Jika pasien tidak ditemukan, hapus sesi dan arahkan ke login
        request.session.flush()
        return redirect('login_pasien')
    
    # Tampilkan ucapan selamat datang dan tautan ke fungsi diagnostik
    context = {
        'pasien': pasien
    }
    
    return render(request, 'dashboard_pasien.html', context)


def edit_akun_pasien(request):
    """
    View untuk mengelola dan memperbarui informasi pribadi Pasien
    """
    # Pastikan pengguna sudah login (cek pasien_id di sesi)
    if 'pasien_id' not in request.session:
        return redirect('login_pasien')
    
    # Ambil data Pasien yang sedang login
    pasien_id = request.session.get('pasien_id')
    try:
        pasien = Pasien.objects.get(id=pasien_id)
    except Pasien.DoesNotExist:
        # Jika pasien tidak ditemukan, hapus sesi dan arahkan ke login
        request.session.flush()
        return redirect('login_pasien')
    
    if request.method == 'GET':
        # Metode GET: Tampilkan formulir yang sudah terisi dengan data Pasien saat ini
        context = {
            'pasien': pasien
        }
        return render(request, 'edit_akun_pasien.html', context)
    
    elif request.method == 'POST':
        # Metode POST: Proses pembaruan data Pasien
        nama = request.POST.get('nama')
        nama_wali = request.POST.get('nama_wali')
        nomor_telepon = request.POST.get('nomor_telepon')
        kata_sandi_baru = request.POST.get('kata_sandi_baru')
        
        # Validasi data
        if not nama:
            context = {
                'pasien': pasien,
                'error': 'Nama tidak boleh kosong'
            }
            return render(request, 'edit_akun_pasien.html', context)
        
        # Update data pasien
        pasien.nama = nama
        pasien.namaWali = nama_wali or None
        pasien.nomorTelepon = nomor_telepon or None
        
        # Jika bidang kataSandi_baru diisi, perbarui kata sandi dengan aman
        if kata_sandi_baru:
            if len(kata_sandi_baru) < 6:
                context = {
                    'pasien': pasien,
                    'error': 'Kata sandi minimal 6 karakter'
                }
                return render(request, 'edit_akun_pasien.html', context)
            pasien.set_password(kata_sandi_baru)
        
        # Simpan perubahan
        pasien.save()
        
        # Berikan pesan sukses dan redirect ke dashboard
        return redirect('dashboard_pasien')


# PROMPT #5: Data Klinis (Input, Z-Score Akurat, & Grafik)
def input_pengukuran(request):
    """
    View untuk input data pengukuran fisik
    """
    # Pastikan pengguna sudah login
    if 'pasien_id' not in request.session:
        return redirect('login_pasien')
    
    # Ambil pasien yang sedang login
    pasien_id = request.session.get('pasien_id')
    pasien = Pasien.objects.get(id=pasien_id)
    
    if request.method == 'GET':
        # Metode GET: Tampilkan formulir untuk input tanggalUkur, beratBadan, dan tinggiBadan
        return render(request, 'input_pengukuran.html')
    
    elif request.method == 'POST':
        # Metode POST: Validasi input dan buat objek PengukuranFisik baru
        tanggal_ukur = request.POST.get('tanggal_ukur')
        berat_badan = request.POST.get('berat_badan')
        tinggi_badan = request.POST.get('tinggi_badan')
        
        # Validasi input
        if not all([tanggal_ukur, berat_badan, tinggi_badan]):
            return render(request, 'input_pengukuran.html', {
                'error': 'Semua field harus diisi',
                'pasien': pasien
            })
        
        try:
            # Buat objek PengukuranFisik baru, hubungkan dengan Pasien yang sedang login
            pengukuran = PengukuranFisik.objects.create(
                pasien=pasien,
                tanggalUkur=tanggal_ukur,
                beratBadan=berat_badan,
                tinggiBadan=tinggi_badan
            )
            
            # Segera panggil hitung_dan_simpan_zscore(pengukuran_id) pada objek baru tersebut
            hitung_dan_simpan_zscore(pengukuran.id)
            
            # Panggil buat_jadwal_notifikasi(pasien_id, tanggal_pengukuran_terakhir) 
            # untuk menjadwalkan pengukuran berikutnya
            buat_jadwal_notifikasi(pasien_id, pengukuran.tanggalUkur)
            
            # Redirect ke dashboard atau halaman grafik
            return redirect('tampilkan_grafik_riwayat', pasien_id=pasien_id)
            
        except Exception as e:
            return render(request, 'input_pengukuran.html', {
                'error': f'Terjadi kesalahan: {str(e)}',
                'pasien': pasien
            })


def tampilkan_grafik_riwayat(request, pasien_id):
    """
    View untuk menampilkan grafik riwayat pengukuran fisik
    
    Args:
        pasien_id: ID pasien
    """
    # Pastikan pengguna sudah login
    if 'pasien_id' not in request.session:
        return redirect('login_pasien')
        
    # Ambil semua data PengukuranFisik untuk pasien_id yang diurutkan berdasarkan tanggal
    pengukuran_list = PengukuranFisik.objects.filter(pasien_id=pasien_id).order_by('tanggalUkur')
    
    # Ubah data menjadi format JSON yang optimal untuk client-side rendering
    data_bb_u = []
    data_tb_u = []
    
    for pengukuran in pengukuran_list:
        data_bb_u.append({
            'tgl': pengukuran.tanggalUkur.strftime('%Y-%m-%d'),
            'score': float(pengukuran.skor_Z_BB_U) if pengukuran.skor_Z_BB_U is not None else None
        })
        
        data_tb_u.append({
            'tgl': pengukuran.tanggalUkur.strftime('%Y-%m-%d'),
            'score': float(pengukuran.skor_Z_TB_U) if pengukuran.skor_Z_TB_U is not None else None
        })
    
    # Kembalikan data untuk rendering grafik di template
    context = {
        'data_bb_u': data_bb_u,
        'data_tb_u': data_tb_u,
        'pasien_id': pasien_id,
    }
    
    return render(request, 'grafik_riwayat.html', context)


# Expert/Admin Views
@login_required
@user_passes_test(is_staff)
def create_rule_group(request):
    """
    View untuk membuat satu Kelompok Aturan (Rule Group) baru
    """
    kondisi_list = Kondisi.objects.all()
    gejala_list = Gejala.objects.all()
    
    if request.method == 'POST':
        # Validasi input
        kondisi_id = request.POST.get('kondisi')
        gejala_ids = request.POST.getlist('gejala')
        kode_kelompok = request.POST.get('kode_kelompok')
        
        if not all([kondisi_id, gejala_ids, kode_kelompok]):
            return render(request, 'pakar_create_rule.html', {
                'kondisi_list': kondisi_list,
                'gejala_list': gejala_list,
                'error': 'Semua field harus diisi'
            })
        
        try:
            # Ambil Kondisi
            kondisi = Kondisi.objects.get(kodeKondisi=kondisi_id)
            
            # Untuk setiap Gejala yang dipilih, buat entri terpisah dalam tabel Aturan
            for gejala_id in gejala_ids:
                gejala = Gejala.objects.get(kodeGejala=gejala_id)
                Aturan.objects.create(
                    kondisi=kondisi,
                    gejala=gejala,
                    kodeKelompokAturan=kode_kelompok
                )
            
            # Redirect ke daftar aturan
            return redirect('list_rules_pakar')
            
        except Exception as e:
            return render(request, 'pakar_create_rule.html', {
                'kondisi_list': kondisi_list,
                'gejala_list': gejala_list,
                'error': f'Terjadi kesalahan: {str(e)}'
            })
    
    # Metode GET: Tampilkan formulir
    return render(request, 'pakar_create_rule.html', {
        'kondisi_list': kondisi_list,
        'gejala_list': gejala_list
    })


@login_required
@user_passes_test(is_staff)
def list_patients_pakar(request):
    """
    View untuk menampilkan daftar semua Pasien
    """
    # Ambil semua pasien
    pasien_list = Pasien.objects.all().order_by('nama')
    
    return render(request, 'pakar_list_patients.html', {
        'pasien_list': pasien_list
    })


@login_required
@user_passes_test(is_staff)
def detail_pasien_pakar(request, pasien_id):
    """
    View untuk menampilkan ringkasan data Pasien untuk Pakar
    """
    # Ambil data pasien
    try:
        pasien = Pasien.objects.get(id=pasien_id)
    except Pasien.DoesNotExist:
        # Jika pasien tidak ditemukan, tampilkan pesan error
        return render(request, 'pakar_list_patients.html', {
            'error': 'Pasien tidak ditemukan'
        })
    
    # Ambil semua data PengukuranFisik
    pengukuran_list = PengukuranFisik.objects.filter(pasien=pasien).order_by('-tanggalUkur')
    
    # Ambil riwayat Konsultasi
    konsultasi_list = Konsultasi.objects.filter(pasien=pasien).order_by('-tanggalKonsultasi')
    
    # Untuk setiap konsultasi, ambil detail gejala
    for konsultasi in konsultasi_list:
        konsultasi.detail_gejala = DetailKonsultasi.objects.filter(konsultasi=konsultasi).select_related('gejala')
    
    return render(request, 'pakar_detail_pasien.html', {
        'pasien': pasien,
        'pengukuran_list': pengukuran_list,
        'konsultasi_list': konsultasi_list
    })


@login_required
@user_passes_test(is_staff)
def list_rules_pakar(request):
    """
    View untuk menampilkan daftar semua Aturan yang terstruktur
    """
    # Ambil semua aturan dan kelompokkan berdasarkan kodeKelompokAturan
    aturan_list = Aturan.objects.select_related('kondisi', 'gejala').order_by('kodeKelompokAturan')
    
    # Kelompokkan aturan berdasarkan kodeKelompokAturan dan kondisi
    aturan_kelompok = defaultdict(list)
    for aturan in aturan_list:
        key = (aturan.kodeKelompokAturan, aturan.kondisi)
        aturan_kelompok[key].append(aturan)
    
    return render(request, 'pakar_list_rules.html', {
        'aturan_kelompok': dict(aturan_kelompok)
    })