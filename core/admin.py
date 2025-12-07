from django.contrib import admin
from .models import Pasien, Gejala, Kondisi, Aturan, Konsultasi, DetailKonsultasi, PengukuranFisik, Notifikasi

# Register your models here.
admin.site.register(Pasien)
admin.site.register(Gejala)
admin.site.register(Kondisi)
admin.site.register(Aturan)
admin.site.register(Konsultasi)
admin.site.register(DetailKonsultasi)
admin.site.register(PengukuranFisik)
admin.site.register(Notifikasi)