from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Pasien, Konsultasi, DetailKonsultasi, Gejala, Kondisi, Aturan, PengukuranFisik

class Command(BaseCommand):
    help = 'Create default users and groups for the SP Stunting system'

    def handle(self, *args, **options):
        # Create Groups
        admin_group, created = Group.objects.get_or_create(name='Admin System')
        if created:
            self.stdout.write(self.style.SUCCESS('Created group: Admin System'))
        else:
            self.stdout.write(self.style.WARNING('Group Admin System already exists'))

        expert_group, created = Group.objects.get_or_create(name='Pakar Diagnosa')
        if created:
            self.stdout.write(self.style.SUCCESS('Created group: Pakar Diagnosa'))
        else:
            self.stdout.write(self.style.WARNING('Group Pakar Diagnosa already exists'))

        # Assign permissions to Pakar Diagnosa group
        # Get content types for core models
        pasien_ct = ContentType.objects.get_for_model(Pasien)
        konsultasi_ct = ContentType.objects.get_for_model(Konsultasi)
        detail_konsultasi_ct = ContentType.objects.get_for_model(DetailKonsultasi)
        gejala_ct = ContentType.objects.get_for_model(Gejala)
        kondisi_ct = ContentType.objects.get_for_model(Kondisi)
        aturan_ct = ContentType.objects.get_for_model(Aturan)
        pengukuran_ct = ContentType.objects.get_for_model(PengukuranFisik)

        # Permissions for Pakar Diagnosa group
        pakar_permissions = [
            # Pasien permissions
            Permission.objects.get(content_type=pasien_ct, codename='view_pasien'),
            
            # Konsultasi permissions
            Permission.objects.get(content_type=konsultasi_ct, codename='view_konsultasi'),
            Permission.objects.get(content_type=konsultasi_ct, codename='change_konsultasi'),
            Permission.objects.get(content_type=konsultasi_ct, codename='add_konsultasi'),
            
            # DetailKonsultasi permissions
            Permission.objects.get(content_type=detail_konsultasi_ct, codename='view_detailkonsultasi'),
            Permission.objects.get(content_type=detail_konsultasi_ct, codename='change_detailkonsultasi'),
            Permission.objects.get(content_type=detail_konsultasi_ct, codename='add_detailkonsultasi'),
            
            # Gejala permissions
            Permission.objects.get(content_type=gejala_ct, codename='view_gejala'),
            Permission.objects.get(content_type=gejala_ct, codename='change_gejala'),
            Permission.objects.get(content_type=gejala_ct, codename='add_gejala'),
            
            # Kondisi permissions
            Permission.objects.get(content_type=kondisi_ct, codename='view_kondisi'),
            Permission.objects.get(content_type=kondisi_ct, codename='change_kondisi'),
            Permission.objects.get(content_type=kondisi_ct, codename='add_kondisi'),
            
            # Aturan permissions
            Permission.objects.get(content_type=aturan_ct, codename='view_aturan'),
            Permission.objects.get(content_type=aturan_ct, codename='change_aturan'),
            Permission.objects.get(content_type=aturan_ct, codename='add_aturan'),
            
            # PengukuranFisik permissions
            Permission.objects.get(content_type=pengukuran_ct, codename='view_pengukuranfisik'),
            Permission.objects.get(content_type=pengukuran_ct, codename='change_pengukuranfisik'),
            Permission.objects.get(content_type=pengukuran_ct, codename='add_pengukuranfisik'),
        ]

        # Clear existing permissions and set new ones for Pakar Diagnosa group
        expert_group.permissions.set(pakar_permissions)
        self.stdout.write(self.style.SUCCESS('Assigned permissions to Pakar Diagnosa group'))

        # Create Admin User
        admin_user, created = User.objects.get_or_create(username='admin')
        if created:
            admin_user.set_password('admin123')
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            admin_user.groups.add(admin_group)
            self.stdout.write(self.style.SUCCESS('Created admin user: admin/admin123'))
        else:
            self.stdout.write(self.style.WARNING('Admin user already exists'))

        # Create Expert User
        expert_user, created = User.objects.get_or_create(username='pakar')
        if created:
            expert_user.set_password('pakar123')
            expert_user.is_staff = True
            expert_user.is_superuser = False
            expert_user.save()
            expert_user.groups.add(expert_group)
            self.stdout.write(self.style.SUCCESS('Created expert user: pakar/pakar123'))
        else:
            self.stdout.write(self.style.WARNING('Expert user already exists'))

        self.stdout.write(self.style.SUCCESS('Default users and groups setup completed successfully!'))