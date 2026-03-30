from django import forms
from .models import Audit, AuditResponse, Observation, Evidence, Warehouse, AuditTemplate


class AuditCreateForm(forms.ModelForm):
    class Meta:
        model = Audit
        fields = ['warehouse', 'template', 'scheduled_date', 'notes']
        labels = {
            'warehouse': 'Bodega',
            'template': 'Plantilla',
            'scheduled_date': 'Fecha programada',
            'notes': 'Notas generales',
        }
        widgets = {
            'scheduled_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'template': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ObservationForm(forms.ModelForm):
    class Meta:
        model = Observation
        fields = ['description', 'severity', 'due_date']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class EvidenceForm(forms.ModelForm):
    class Meta:
        model = Evidence
        fields = ['image', 'caption']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'caption': forms.TextInput(attrs={'class': 'form-control'}),
        }


def build_response_form(audit_item):
    """Dynamically build a single-field form for an AuditItem."""
    if audit_item.item_type == 'boolean':
        field = forms.NullBooleanField(
            label=audit_item.question,
            required=audit_item.required,
            widget=forms.Select(
                choices=[('', '-- Seleccionar --'), (True, 'Sí'), (False, 'No')],
                attrs={'class': 'form-select'},
            ),
        )
    elif audit_item.item_type == 'number':
        field = forms.FloatField(
            label=audit_item.question,
            required=audit_item.required,
            widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
        )
    else:
        field = forms.CharField(
            label=audit_item.question,
            required=audit_item.required,
            widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        )
    return field


class AuditResponseFormSet(forms.BaseFormSet):
    pass
