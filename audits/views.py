from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse

from .models import Audit, AuditItem, AuditResponse, Observation, Evidence, Warehouse, AuditTemplate
from .forms import AuditCreateForm, ObservationForm, EvidenceForm, build_response_form


@login_required
def audit_list(request):
    audits = Audit.objects.select_related('warehouse', 'auditor').all()
    status_filter = request.GET.get('status', '')
    warehouse_filter = request.GET.get('warehouse', '')
    if status_filter:
        audits = audits.filter(status=status_filter)
    if warehouse_filter:
        audits = audits.filter(warehouse_id=warehouse_filter)
    warehouses = Warehouse.objects.filter(active=True)
    context = {
        'audits': audits,
        'warehouses': warehouses,
        'status_filter': status_filter,
        'warehouse_filter': warehouse_filter,
        'status_choices': Audit.STATUS_CHOICES,
    }
    return render(request, 'audit_list.html', context)


@login_required
def audit_create(request):
    if request.method == 'POST':
        form = AuditCreateForm(request.POST)
        if form.is_valid():
            audit = form.save(commit=False)
            audit.auditor = request.user
            audit.status = 'in_progress'
            audit.save()
            messages.success(request, 'Auditoría creada. Complete el checklist.')
            return redirect('audits:audit_checklist', pk=audit.pk)
    else:
        form = AuditCreateForm()
    return render(request, 'audit_form.html', {'form': form, 'title': 'Nueva Auditoría'})


@login_required
def audit_checklist(request, pk):
    audit = get_object_or_404(Audit, pk=pk)
    if audit.status == 'completed':
        messages.info(request, 'La auditoria ya esta completada. Se muestra el detalle final.')
        return redirect('audits:audit_detail', pk=audit.pk)

    items = audit.template.items.all()

    # Build dynamic fields dict keyed by item.pk
    field_definitions = {item.pk: build_response_form(item) for item in items}

    if request.method == 'POST':
        errors = []
        for item in items:
            key = f'item_{item.pk}'
            raw = request.POST.get(key)
            response, _ = AuditResponse.objects.get_or_create(audit=audit, item=item)
            if item.item_type == 'boolean':
                if raw in ['True', 'true', '1']:
                    response.boolean_value = True
                elif raw in ['False', 'false', '0']:
                    response.boolean_value = False
                else:
                    response.boolean_value = None
            elif item.item_type == 'number':
                try:
                    response.number_value = float(raw) if raw else None
                except ValueError:
                    response.number_value = None
            else:
                response.text_value = raw or ''
            response.save()

        # Recalculate compliance
        responses = AuditResponse.objects.filter(audit=audit, item__item_type='boolean')
        total_bool = responses.count()
        ok_count = responses.filter(boolean_value=True).count()
        audit.compliance_pct = round((ok_count / total_bool * 100), 1) if total_bool else 100.0

        action = request.POST.get('action', 'save')
        if action == 'complete':
            audit.status = 'completed'
            audit.completed_date = timezone.now()
            critical_obs = audit.observations.filter(severity='high').count()
            if critical_obs > 0:
                audit.result = 'critical'
            elif audit.compliance_pct < 80:
                audit.result = 'with_observations'
            else:
                audit.result = 'ok'
        audit.save()
        messages.success(request, 'Respuestas guardadas.')
        if action == 'complete':
            return redirect('audits:audit_detail', pk=audit.pk)
        return redirect('audits:audit_checklist', pk=audit.pk)

    # Attach existing responses to items
    existing = {r.item_id: r for r in audit.responses.all()}
    items_with_fields = []
    for item in items:
        resp = existing.get(item.pk)
        current_value = None
        if resp:
            if item.item_type == 'boolean':
                current_value = resp.boolean_value
            elif item.item_type == 'number':
                current_value = resp.number_value
            else:
                current_value = resp.text_value
        items_with_fields.append({
            'item': item,
            'field_name': f'item_{item.pk}',
            'current_value': current_value,
        })

    context = {
        'audit': audit,
        'items_with_fields': items_with_fields,
    }
    return render(request, 'audit_checklist.html', context)


@login_required
def audit_detail(request, pk):
    audit = get_object_or_404(Audit, pk=pk)
    responses = audit.responses.select_related('item').all()
    observations = audit.observations.all()
    evidences = audit.evidences.all()

    obs_form = ObservationForm()
    evidence_form = EvidenceForm()

    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'observation':
            obs_form = ObservationForm(request.POST)
            if obs_form.is_valid():
                obs = obs_form.save(commit=False)
                obs.audit = audit
                obs.save()
                messages.success(request, 'Observación guardada.')
                return redirect('audits:audit_detail', pk=pk)
        elif form_type == 'evidence':
            evidence_form = EvidenceForm(request.POST, request.FILES)
            if evidence_form.is_valid():
                ev = evidence_form.save(commit=False)
                ev.audit = audit
                ev.save()
                messages.success(request, 'Imagen subida correctamente.')
                return redirect('audits:audit_detail', pk=pk)

    context = {
        'audit': audit,
        'responses': responses,
        'observations': observations,
        'evidences': evidences,
        'obs_form': obs_form,
        'evidence_form': evidence_form,
    }
    return render(request, 'audit_detail.html', context)


@login_required
def observation_resolve(request, pk):
    obs = get_object_or_404(Observation, pk=pk)
    obs.resolved = True
    obs.save()
    messages.success(request, 'Observación marcada como resuelta.')
    return redirect('audits:audit_detail', pk=obs.audit_id)
