from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import InventoryRecord, Product
from .forms import InventoryRecordForm
from audits.models import Warehouse


@login_required
def inventory_list(request):
    warehouse_id = request.GET.get('warehouse', '')
    warehouses = Warehouse.objects.filter(active=True)
    records = InventoryRecord.objects.select_related('product', 'warehouse', 'product__category')
    if warehouse_id:
        records = records.filter(warehouse_id=warehouse_id)

    if request.method == 'POST':
        record_id = request.POST.get('record_id')
        record = get_object_or_404(InventoryRecord, pk=record_id)
        form = InventoryRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, f'Inventario de {record.product.name} actualizado.')
        else:
            messages.error(request, 'Error al guardar. Revise los datos.')
        return redirect(request.get_full_path())

    records_with_forms = [(rec, InventoryRecordForm(instance=rec)) for rec in records]

    context = {
        'records_with_forms': records_with_forms,
        'warehouses': warehouses,
        'warehouse_filter': warehouse_id,
    }
    return render(request, 'inventory.html', context)
