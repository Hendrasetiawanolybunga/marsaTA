from django.contrib.auth.models import User
from .models import Pasien, Gejala, Kondisi, Aturan, PengukuranFisik
from datetime import date

def create_sample_data():
    # Create sample patients
    pasien1 = Pasien(
        namaPengguna="balita1",
        nama="Andi Susanto",
        jenisKelamin="L",
        tanggalLahir=date(2020, 5, 15),
        namaWali="Budi Susanto",
        nomorTelepon="08123456789"
    )
    pasien1.set_password("password123")  # Use the new password hashing method
    pasien1.save()
    
    # Create sample symptoms (gejala)
    gejala_list = [
        {"kodeGejala": "G01", "namaGejala": "Tinggi badan kurang dari normal"},
        {"kodeGejala": "G02", "namaGejala": "Berat badan kurang dari normal"},
        {"kodeGejala": "G03", "namaGejala": "Nafsu makan rendah"},
        {"kodeGejala": "G04", "namaGejala": "Sering sakit"},
        {"kodeGejala": "G05", "namaGejala": "Perkembangan motorik lambat"},
        {"kodeGejala": "G06", "namaGejala": "Kulit keriput"},
        {"kodeGejala": "G07", "namaGejala": "Rambut tipis dan mudah rontok"},
    ]
    
    for gejala_data in gejala_list:
        Gejala.objects.create(**gejala_data)
    
    # Create sample conditions (kondisi)
    kondisi_stunting = Kondisi.objects.create(
        kodeKondisi="K01",
        namaKondisi="Stunting Sedang",
        deskripsi="Anak mengalami gangguan pertumbuhan dengan tinggi badan kurang dari normal untuk usia.",
        solusi="Perbaiki pola makan dengan makanan bergizi seimbang, berikan ASI eksklusif sampai 6 bulan, dan konsultasi rutin ke dokter."
    )
    
    kondisi_normal = Kondisi.objects.create(
        kodeKondisi="K02",
        namaKondisi="Normal",
        deskripsi="Anak memiliki pertumbuhan yang normal sesuai standar.",
        solusi="Pertahankan pola makan bergizi seimbang dan gaya hidup sehat."
    )
    
    # Create sample rules (aturan)
    # Rules for Stunting (K01)
    Aturan.objects.create(
        kondisi=kondisi_stunting,
        gejala=Gejala.objects.get(kodeGejala="G01"),
        kodeKelompokAturan="R01",
        keterangan="Gejala utama stunting"
    )
    
    Aturan.objects.create(
        kondisi=kondisi_stunting,
        gejala=Gejala.objects.get(kodeGejala="G02"),
        kodeKelompokAturan="R01",
        keterangan="Gejala pendukung stunting"
    )
    
    # Rules for Normal (K02) - more complex rule
    Aturan.objects.create(
        kondisi=kondisi_normal,
        gejala=Gejala.objects.get(kodeGejala="G02"),
        kodeKelompokAturan="R02",
        keterangan="Tidak menunjukkan gejala kurang gizi"
    )
    
    Aturan.objects.create(
        kondisi=kondisi_normal,
        gejala=Gejala.objects.get(kodeGejala="G03"),
        kodeKelompokAturan="R02",
        keterangan="Memiliki nafsu makan yang baik"
    )
    
    Aturan.objects.create(
        kondisi=kondisi_normal,
        gejala=Gejala.objects.get(kodeGejala="G05"),
        kodeKelompokAturan="R02",
        keterangan="Perkembangan motorik normal"
    )
    
    print("Sample data created successfully!")

if __name__ == "__main__":
    create_sample_data()