from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Warehouse(models.Model):
    name = models.CharField(max_length=150, verbose_name='Nombre')
    location = models.CharField(max_length=200, verbose_name='Ubicación')
    manager = models.CharField(max_length=150, blank=True, verbose_name='Encargado')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Bodega'
        verbose_name_plural = 'Bodegas'
        ordering = ['name']

    def __str__(self):
        return self.name


class AuditTemplate(models.Model):
    name = models.CharField(max_length=150, verbose_name='Nombre del Template')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Template de Auditoría'
        verbose_name_plural = 'Templates de Auditoría'

    def __str__(self):
        return self.name


class AuditItem(models.Model):
    ITEM_TYPES = [
        ('boolean', 'Sí / No'),
        ('text', 'Texto'),
        ('number', 'Número'),
    ]
    template = models.ForeignKey(AuditTemplate, on_delete=models.CASCADE, related_name='items')
    question = models.CharField(max_length=300, verbose_name='Pregunta')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES, default='boolean')
    order = models.PositiveIntegerField(default=0)
    required = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Ítem de Auditoría'
        verbose_name_plural = 'Ítems de Auditoría'

    def __str__(self):
        return self.question


class Audit(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
    ]
    RESULT_CHOICES = [
        ('ok', 'OK'),
        ('with_observations', 'Con Observaciones'),
        ('critical', 'Crítica'),
    ]
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='audits')
    template = models.ForeignKey(AuditTemplate, on_delete=models.CASCADE)
    auditor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, blank=True)
    compliance_pct = models.FloatField(default=0.0, verbose_name='% Cumplimiento')
    scheduled_date = models.DateField(default=timezone.now)
    completed_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, verbose_name='Notas generales')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Auditoría'
        verbose_name_plural = 'Auditorías'
        ordering = ['-created_at']

    def __str__(self):
        return f'Auditoría {self.pk} – {self.warehouse.name} ({self.get_status_display()})'

    def calculate_compliance(self):
        responses = self.responses.all()
        total = responses.count()
        if total == 0:
            return 0.0
        ok = responses.filter(boolean_value=True).count()
        text_ok = responses.exclude(text_value='').exclude(text_value=None).count()
        boolean_items = responses.filter(item__item_type='boolean').count()
        if boolean_items == 0:
            return 100.0
        return round((ok / boolean_items) * 100, 1)

    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.result:
            pct = self.calculate_compliance()
            self.compliance_pct = pct
            critical_obs = self.observations.filter(severity='high').count()
            if critical_obs > 0:
                self.result = 'critical'
            elif pct < 80:
                self.result = 'with_observations'
            else:
                self.result = 'ok'
        super().save(*args, **kwargs)


class AuditResponse(models.Model):
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='responses')
    item = models.ForeignKey(AuditItem, on_delete=models.CASCADE)
    boolean_value = models.BooleanField(null=True, blank=True)
    text_value = models.TextField(blank=True)
    number_value = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ('audit', 'item')

    def __str__(self):
        return f'{self.item.question[:40]} – {self.audit}'


class Observation(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
    ]
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='observations')
    description = models.TextField(verbose_name='Descripción')
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    due_date = models.DateField(null=True, blank=True, verbose_name='Fecha compromiso')
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Observación'
        verbose_name_plural = 'Observaciones'
        ordering = ['-created_at']

    def __str__(self):
        return self.description[:60]

    @property
    def is_overdue(self):
        if self.due_date and not self.resolved:
            return self.due_date < timezone.now().date()
        return False


class Evidence(models.Model):
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='evidences')
    observation = models.ForeignKey(Observation, on_delete=models.SET_NULL, null=True, blank=True, related_name='evidences')
    image = models.ImageField(upload_to='evidences/%Y/%m/', verbose_name='Imagen')
    caption = models.CharField(max_length=200, blank=True, verbose_name='Descripción')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Evidencia'
        verbose_name_plural = 'Evidencias'

    def __str__(self):
        return f'Evidencia {self.pk} – {self.audit}'
