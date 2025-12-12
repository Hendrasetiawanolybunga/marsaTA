import random
from datetime import timedelta, date
from .models import Pasien, PengukuranFisik, Notifikasi

def hitung_dan_simpan_zscore(pengukuran_id):
    """
    Fungsi untuk menghitung dan menyimpan Z-Score dari pengukuran fisik
    
    Args:
        pengukuran_id: ID dari objek PengukuranFisik yang baru diinput
        
    Returns:
        Objek PengukuranFisik yang telah diupdate dengan Z-Score
    """
    try:
        # Terima pengukuran_id dari objek PengukuranFisik yang baru diinput
        pengukuran = PengukuranFisik.objects.get(id=pengukuran_id)
    except PengukuranFisik.DoesNotExist:
        raise ValueError("Pengukuran tidak ditemukan")
    
    try:
        # Ambil tanggalLahir, jenisKelamin (dari Pasien), beratBadan, dan tinggiBadan (dari PengukuranFisik)
        pasien = pengukuran.pasien
        tanggal_lahir = pasien.tanggalLahir
        jenis_kelamin = pasien.jenisKelamin
        berat_badan = float(pengukuran.beratBadan)
        tinggi_badan = float(pengukuran.tinggiBadan)
        tanggal_ukur = pengukuran.tanggalUkur
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Data pengukuran tidak valid: {str(e)}")
    
    # Hitung Usia Anak dalam bulan (umur_bulan) dari tanggalLahir Pasien dan tanggalUkur
    umur_bulan = (tanggal_ukur.year - tanggal_lahir.year) * 12 + (tanggal_ukur.month - tanggal_lahir.month)
    
    # Validasi umur (harus positif dan masuk akal)
    if umur_bulan < 0:
        raise ValueError("Tanggal pengukuran tidak valid - tanggal pengukuran sebelum tanggal lahir pasien")
    
    # Validasi umur tidak terlalu besar (misalnya lebih dari 20 tahun)
    if umur_bulan > 240:  # 20 tahun
        raise ValueError("Tanggal pengukuran tidak valid - usia anak terlalu besar")
    
    # Simulasi Lookup Tabel Z-Score: 
    # Tampilkan placeholder di kode yang menunjukkan bagaimana nilai SD (+2, -2, dll.) 
    # akan dicari berdasarkan umur_bulan dan jenisKelamin.
    
    # Placeholder untuk simulasi lookup tabel Z-Score WHO
    # Dalam implementasi nyata, ini akan melibatkan tabel referensi WHO
    # Berdasarkan umur_bulan dan jenisKelamin, kita akan mendapatkan:
    # median_berat, sd_berat, median_tinggi, sd_tinggi
    
    # Untuk simulasi, kita gunakan nilai acak namun realistis berdasarkan umur
    if umur_bulan <= 24:  # Bayi 0-24 bulan
        median_berat = 0.5 * umur_bulan + 3.0
        sd_berat = 0.2 * umur_bulan + 0.5
        median_tinggi = 2.0 * umur_bulan + 45.0
        sd_tinggi = 0.3 * umur_bulan + 1.0
    elif umur_bulan <= 60:  # Balita 2-5 tahun
        median_berat = 0.2 * umur_bulan + 7.0
        sd_berat = 0.15 * umur_bulan + 0.8
        median_tinggi = 1.5 * umur_bulan + 65.0
        sd_tinggi = 0.2 * umur_bulan + 1.2
    else:  # Anak > 5 tahun
        median_berat = 0.15 * umur_bulan + 10.0
        sd_berat = 0.1 * umur_bulan + 1.0
        median_tinggi = 1.2 * umur_bulan + 80.0
        sd_tinggi = 0.15 * umur_bulan + 1.5
    
    # Hitung Z-Score menggunakan rumus: (nilai - median) / SD
    try:
        z_score_bb_u = round((berat_badan - median_berat) / sd_berat, 2)
        z_score_tb_u = round((tinggi_badan - median_tinggi) / sd_tinggi, 2)
    except ZeroDivisionError:
        raise ValueError("Terjadi kesalahan dalam perhitungan Z-Score")
    
    # Batasi nilai Z-Score agar realistis (biasanya antara -3 dan +3)
    z_score_bb_u = max(min(z_score_bb_u, 3.0), -3.0)
    z_score_tb_u = max(min(z_score_tb_u, 3.0), -3.0)
    
    # Simpan hasil Z-Score yang dihitung kembali ke objek PengukuranFisik
    pengukuran.skor_Z_BB_U = z_score_bb_u
    pengukuran.skor_Z_TB_U = z_score_tb_u
    pengukuran.save()
    
    return pengukuran


def buat_jadwal_notifikasi(pasien_id, tanggal_pengukuran_terakhir):
    """
    Fungsi untuk membuat jadwal notifikasi pengukuran ulang
    
    Args:
        pasien_id: ID pasien
        tanggal_pengukuran_terakhir: Tanggal pengukuran terakhir
        
    Returns:
        Objek Notifikasi yang telah dibuat
    """
    try:
        # Terima pasien_id dan tanggal pengukuran terakhir
        pasien = Pasien.objects.get(id=pasien_id)
    except Pasien.DoesNotExist:
        raise ValueError("Pasien tidak ditemukan")
    
    # Validasi tanggal
    if not isinstance(tanggal_pengukuran_terakhir, date):
        raise ValueError("Tanggal pengukuran tidak valid")
    
    # Logika Jadwal: Hitung tanggal pengukuran ulang berikutnya (misalnya, 30 hari setelah tanggal_pengukuran_terakhir)
    tanggal_pengukuran_ulang = tanggal_pengukuran_terakhir + timedelta(days=30)
    
    # Buat objek Notifikasi baru untuk pasien_id tersebut
    notifikasi = Notifikasi.objects.create(
        pasien=pasien,
        judul="Jadwal Pengukuran Ulang",
        pesan="Saatnya melakukan pengukuran ulang pertumbuhan anak Anda.",
        jadwalNotifikasi=tanggal_pengukuran_ulang,
        tipe='pengukuran_ulang'
    )
    
    return notifikasi