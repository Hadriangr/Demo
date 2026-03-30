from django import forms
from audits.models import Warehouse
from .models import InventoryRecord


class InventoryRecordForm(forms.ModelForm):
    class Meta:
        model = InventoryRecord
        fields = ['expected_stock', 'counted_stock', 'damaged_stock']
        widgets = {
            'expected_stock': forms.NumberInput(attrs={'class': 'form-control form-control-sm inventory-numeric-input', 'min': 0}),
            'counted_stock': forms.NumberInput(attrs={'class': 'form-control form-control-sm inventory-numeric-input', 'min': 0}),
            'damaged_stock': forms.NumberInput(attrs={'class': 'form-control form-control-sm inventory-numeric-input', 'min': 0}),
        }


class InventoryProductCreateForm(forms.Form):
    name = forms.CharField(
        label='Producto',
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Casco dieléctrico'})
    )
    sku = forms.CharField(
        label='SKU',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: OB-CAS-011'})
    )
    category_name = forms.CharField(
        label='Categoría',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: EPP y Vestimenta'})
    )
    unit = forms.CharField(
        label='Unidad',
        max_length=30,
        initial='unidades',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    warehouse = forms.ModelChoiceField(
        label='Bodega',
        queryset=Warehouse.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    expected_stock = forms.IntegerField(
        label='Stock esperado',
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    counted_stock = forms.IntegerField(
        label='Stock contado',
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    damaged_stock = forms.IntegerField(
        label='Unidades dañadas',
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        label='Notas',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'})
    )

    def __init__(self, *args, **kwargs):
        warehouses = kwargs.pop('warehouses', None)
        super().__init__(*args, **kwargs)
        if warehouses is not None:
            self.fields['warehouse'].queryset = warehouses

    def clean_sku(self):
        return self.cleaned_data['sku'].strip().upper()
