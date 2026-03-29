"""
Management command to populate the database with demo data.
Run with: python manage.py seed_demo
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
import random


class Command(BaseCommand):
    help = 'Populates the database with demo data for warehouse audit system'

    def handle(self, *args, **options):
        self.stdout.write('Seeding demo data...')

        from audits.models import (
            Warehouse, AuditTemplate, AuditItem,
            Audit, AuditResponse, Observation, Evidence
        )
        from inventory.models import Category, Product, InventoryRecord

        # ── Users ──────────────────────────────────────────────────────
        admin, created = User.objects.get_or_create(username='admin')
        if created or not admin.check_password('password123'):
            admin.set_password('password123')
            admin.first_name = 'Admin'
            admin.last_name = 'Demo'
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()
            self.stdout.write('  ✓ Usuario admin creado')

        auditor, created = User.objects.get_or_create(username='auditor1')
        auditor.set_password('password123')
        auditor.first_name = 'Pablo'
        auditor.last_name = 'Perez'
        auditor.save()
        if created:
            self.stdout.write('  ✓ Usuario auditor1 creado')
        else:
            self.stdout.write('  ✓ Usuario auditor1 actualizado a Pablo Perez')

        # ── Warehouses ─────────────────────────────────────────────────
        wh1, _ = Warehouse.objects.get_or_create(
            name='Bodega Central Norte',
            defaults={'location': 'Av. Industrial 1234, Santiago', 'manager': 'Luis Pérez', 'active': True}
        )
        wh2, _ = Warehouse.objects.get_or_create(
            name='Bodega Sur Express',
            defaults={'location': 'Camino a Melipilla km 12, Santiago', 'manager': 'Ana Díaz', 'active': True}
        )
        self.stdout.write(f'  ✓ Bodegas: {wh1.name}, {wh2.name}')

        # ── Template ──────────────────────────────────────────────────
        tmpl, created = AuditTemplate.objects.get_or_create(
            name='Auditoría de Bodega Estándar'
        )
        if created:
            tmpl.description = 'Checklist estándar para auditorías de bodegas'
            tmpl.save()

        items_data = [
            ('¿El área de recepción está limpia y ordenada?', 'boolean'),
            ('¿Los productos están correctamente etiquetados?', 'boolean'),
            ('¿Las vías de evacuación están despejadas?', 'boolean'),
            ('¿Los extintores están vigentes y accesibles?', 'boolean'),
            ('¿El sistema de iluminación funciona correctamente?', 'boolean'),
            ('¿Los productos perecibles están en temperatura adecuada?', 'boolean'),
            ('¿Se cumplen las normas de apilamiento?', 'boolean'),
            ('Temperatura registrada en cámara fría (°C)', 'number'),
            ('¿El personal usa EPP correctamente?', 'boolean'),
            ('¿Los registros de entrada/salida están al día?', 'boolean'),
            ('Observaciones adicionales del área de almacenamiento', 'text'),
        ]
        if not tmpl.items.exists():
            for i, (question, itype) in enumerate(items_data):
                AuditItem.objects.create(
                    template=tmpl,
                    question=question,
                    item_type=itype,
                    order=i,
                    required=(itype != 'text'),
                )
            self.stdout.write('  ✓ Template e ítems creados')

        # ── Audits ────────────────────────────────────────────────────
        today = timezone.now().date()
        audits_config = [
            # (warehouse, scheduled_date_offset_days, status, compliance, result)
            (wh1, -30, 'completed', 92.0, 'ok'),
            (wh1, -15, 'completed', 64.0, 'with_observations'),
            (wh2, -20, 'completed', 45.0, 'critical'),
            (wh2, -5, 'in_progress', 0.0, ''),
            (wh1, 7, 'pending', 0.0, ''),
        ]
        created_audits = []
        for wh, day_offset, status, compliance, result in audits_config:
            scheduled = today + datetime.timedelta(days=day_offset)
            audit = Audit.objects.create(
                warehouse=wh,
                template=tmpl,
                auditor=auditor,
                status=status,
                result=result,
                compliance_pct=compliance,
                scheduled_date=scheduled,
                completed_date=timezone.now() + datetime.timedelta(days=day_offset) if status == 'completed' else None,
                notes='Auditoría generada como datos de demostración.',
            )
            created_audits.append(audit)

        self.stdout.write(f'  ✓ {len(created_audits)} auditorías creadas')

        # ── Responses for completed audits ───────────────────────────
        boolean_items = AuditItem.objects.filter(template=tmpl, item_type='boolean')
        number_items = AuditItem.objects.filter(template=tmpl, item_type='number')
        text_items = AuditItem.objects.filter(template=tmpl, item_type='text')

        # Audit 0: 92% – mostly ok
        patterns = [
            {i.pk: True for i in boolean_items},   # all true initially
        ]
        patterns[0][boolean_items[1].pk] = False  # one fail

        # Audit 1: 64%
        half_true = {i.pk: (idx % 3 != 0) for idx, i in enumerate(boolean_items)}

        # Audit 2: 45% + critical obs
        mostly_false = {i.pk: (idx % 2 == 0) for idx, i in enumerate(boolean_items)}

        for audit_idx, (audit, bool_map) in enumerate(zip(
            created_audits[:3], [patterns[0], half_true, mostly_false]
        )):
            for item in boolean_items:
                AuditResponse.objects.get_or_create(
                    audit=audit, item=item,
                    defaults={'boolean_value': bool_map.get(item.pk, True)}
                )
            for item in number_items:
                AuditResponse.objects.get_or_create(
                    audit=audit, item=item,
                    defaults={'number_value': round(random.uniform(-5.0, 4.0), 1)}
                )
            for item in text_items:
                AuditResponse.objects.get_or_create(
                    audit=audit, item=item,
                    defaults={'text_value': 'Sin observaciones adicionales.'}
                )

        self.stdout.write('  ✓ Respuestas del checklist creadas')

        # ── Observations ─────────────────────────────────────────────
        obs_data = [
            (created_audits[0], 'Producto sin etiqueta detectado en zona B', 'low', today + datetime.timedelta(days=10), False),
            (created_audits[1], 'Extintores vencidos en pasillo central', 'high', today - datetime.timedelta(days=5), False),
            (created_audits[1], 'Apilamiento incorrecto en zona de alta rotación', 'medium', today + datetime.timedelta(days=15), False),
            (created_audits[2], 'Temperatura de cámara fuera de rango (+8°C)', 'high', today - datetime.timedelta(days=2), False),
            (created_audits[2], 'Falta iluminación en zona de carga', 'high', today + datetime.timedelta(days=3), False),
            (created_audits[2], 'Personal sin EPP en área de productos químicos', 'medium', today + datetime.timedelta(days=5), False),
        ]
        for audit, desc, sev, due, resolved in obs_data:
            Observation.objects.get_or_create(
                audit=audit,
                description=desc,
                defaults={'severity': sev, 'due_date': due, 'resolved': resolved}
            )
        self.stdout.write('  ✓ Observaciones creadas')

        # ── Inventory (EPP y herramientas de obra) ───────────────────
        InventoryRecord.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()

        cat_epp, _ = Category.objects.get_or_create(name='EPP y Vestimenta')
        cat_herramientas, _ = Category.objects.get_or_create(name='Herramientas de Trabajo')

        products_data = [
            ('Casco de seguridad tipo obra', 'OB-CAS-001', cat_epp, 'unidades'),
            ('Botas de seguridad punta de acero', 'OB-BOT-002', cat_epp, 'pares'),
            ('Chaleco reflectante clase 2', 'OB-CHA-003', cat_epp, 'unidades'),
            ('Guantes anticorte nivel 5', 'OB-GUA-004', cat_epp, 'pares'),
            ('Arnes de seguridad 4 puntos', 'OB-ARN-005', cat_epp, 'unidades'),
            ('Martillo demoledor', 'OB-MAR-006', cat_herramientas, 'unidades'),
            ('Taladro percutor industrial', 'OB-TAL-007', cat_herramientas, 'unidades'),
            ('Esmeril angular 7 pulgadas', 'OB-ESM-008', cat_herramientas, 'unidades'),
            ('Juego de llaves mixtas', 'OB-LLA-009', cat_herramientas, 'sets'),
            ('Cinta metrica 8m', 'OB-CIN-010', cat_herramientas, 'unidades'),
        ]
        for name, sku, cat, unit in products_data:
            Product.objects.get_or_create(name=name, defaults={'sku': sku, 'category': cat, 'unit': unit})

        current_month = today.month
        for product in Product.objects.all():
            for wh in [wh1, wh2]:
                expected = random.randint(20, 200)
                counted = max(expected + random.randint(-25, 8), 0)
                damaged = random.randint(0, 8)

                # Force a few out-of-stock alerts in the current month for dashboard Top 5.
                if random.random() < 0.22:
                    counted = 0

                record = InventoryRecord.objects.create(
                    product=product,
                    warehouse=wh,
                    expected_stock=expected,
                    counted_stock=counted,
                    damaged_stock=damaged,
                    notes='Revisar desgaste por uso en terreno.' if damaged > 0 else '',
                )

                # Spread records over recent months to make monthly charts meaningful.
                month_offset = random.randint(0, 5)
                record_month = current_month - month_offset
                record_year = today.year
                if record_month <= 0:
                    record_month += 12
                    record_year -= 1
                day = min(today.day, 28)
                record_date = datetime.datetime(record_year, record_month, day, 10, 0, 0)
                if timezone.is_naive(record_date):
                    record_date = timezone.make_aware(record_date)
                InventoryRecord.objects.filter(pk=record.pk).update(recorded_at=record_date)
        self.stdout.write('  ✓ Productos e inventario creados')

        self.stdout.write(self.style.SUCCESS(
            '\n¡Demo listo! Inicia con: python manage.py runserver\n'
            'Login: admin / password123'
        ))
