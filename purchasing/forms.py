from django import forms
from django.forms import inlineformset_factory

from .models import Purchase, PurchaseDetail


class PurchaseForm(forms.ModelForm):
    """Formulario para la cabecera de compra."""
    class Meta:
        model = Purchase
        fields = ['supplier', 'document_number']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
class PurchaseDetailForm(forms.ModelForm):
    """Línea de compra. Quita el initial de quantity para que las filas vacías
    NO se validen como obligatorias (permite compras con 1 solo producto)."""
    class Meta:
        model = PurchaseDetail
        fields = ['product', 'quantity', 'unit_cost']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['quantity'].initial = None


# Formset: múltiples líneas de detalle dentro de UNA compra
PurchaseDetailFormSet = inlineformset_factory(
    Purchase,
    PurchaseDetail,
    form=PurchaseDetailForm,
    extra=3,
    can_delete=True,
)