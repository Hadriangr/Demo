from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Category, InventoryRecord, Product
from .forms import InventoryRecordForm, InventoryProductCreateForm
from audits.models import Warehouse


@login_required
def inventory_list(request):
    warehouse_id = request.GET.get('warehouse', '')
    warehouses = Warehouse.objects.filter(active=True)
    records = InventoryRecord.objects.select_related('product', 'warehouse', 'product__category')
    if warehouse_id:
        records = records.filter(warehouse_id=warehouse_id)

    create_form = InventoryProductCreateForm(warehouses=warehouses)

    if request.method == 'POST':
        form_type = request.POST.get('form_type', 'update_record')

        if form_type == 'add_product':
            create_form = InventoryProductCreateForm(request.POST, warehouses=warehouses)
            if create_form.is_valid():
                category_name = create_form.cleaned_data['category_name'].strip()
                category, _ = Category.objects.get_or_create(name=category_name)

                product, created = Product.objects.get_or_create(
                    sku=create_form.cleaned_data['sku'],
                    defaults={
                        'name': create_form.cleaned_data['name'].strip(),
                        'category': category,
                        'unit': create_form.cleaned_data['unit'].strip(),
                        'active': True,
                    }
                )

                if not created:
                    product.name = create_form.cleaned_data['name'].strip()
                    product.category = category
                    product.unit = create_form.cleaned_data['unit'].strip()
                    product.active = True
                    product.save()

                record, rec_created = InventoryRecord.objects.update_or_create(
                    product=product,
                    warehouse=create_form.cleaned_data['warehouse'],
                    defaults={
                        'expected_stock': create_form.cleaned_data['expected_stock'],
                        'counted_stock': create_form.cleaned_data['counted_stock'],
                        'damaged_stock': create_form.cleaned_data['damaged_stock'],
                        'notes': create_form.cleaned_data['notes'],
                    }
                )

                if rec_created:
                    messages.success(request, f'Producto {product.name} agregado al inventario.')
                else:
                    messages.success(request, f'Inventario de {product.name} actualizado en {record.warehouse.name}.')
                return redirect(request.get_full_path())
            messages.error(request, 'No se pudo agregar el producto. Revisa los campos del formulario.')
        else:
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
        'create_form': create_form,
    }
    return render(request, 'inventory.html', context)
