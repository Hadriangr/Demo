from django.contrib import admin
from .models import Warehouse, AuditTemplate, AuditItem, Audit, AuditResponse, Observation, Evidence


class AuditItemInline(admin.TabularInline):
    model = AuditItem
    extra = 1


class AuditResponseInline(admin.TabularInline):
    model = AuditResponse
    extra = 0


class ObservationInline(admin.TabularInline):
    model = Observation
    extra = 0


class EvidenceInline(admin.TabularInline):
    model = Evidence
    extra = 0


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'manager', 'active')
    list_filter = ('active',)
    search_fields = ('name', 'location')


@admin.register(AuditTemplate)
class AuditTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    inlines = [AuditItemInline]


@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'warehouse', 'status', 'result', 'compliance_pct', 'scheduled_date')
    list_filter = ('status', 'result', 'warehouse')
    search_fields = ('warehouse__name',)
    inlines = [AuditResponseInline, ObservationInline, EvidenceInline]


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display = ('description', 'audit', 'severity', 'due_date', 'resolved')
    list_filter = ('severity', 'resolved')
