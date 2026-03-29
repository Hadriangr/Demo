from django import forms
from .models import InventoryRecord


class InventoryRecordForm(forms.ModelForm):
    class Meta:
        model = InventoryRecord
        fields = ['expected_stock', 'counted_stock', 'damaged_stock', 'notes']
        widgets = {
            'expected_stock': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': 0}),
            'counted_stock': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': 0}),
            'damaged_stock': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': 0}),
            'notes': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }
