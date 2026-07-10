from decimal import Decimal, ROUND_HALF_UP

from django import forms
from django.forms import inlineformset_factory

from .models import Transaccion, TransaccionDetail

TAX_RATE = Decimal('0.15')
CENTS = Decimal('0.01')


class TransaccionForm(forms.ModelForm):
    class Meta:
        model = Transaccion
        fields = ['tipo', 'descripcion']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Venta de productos varios'}),
        }
        labels = {
            'tipo': 'Tipo de transacción',
            'descripcion': 'Descripción',
        }


class TransaccionDetailForm(forms.ModelForm):
    class Meta:
        model = TransaccionDetail
        fields = ['product', 'quantity', 'unit_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['quantity'].initial = None


TransaccionDetailFormSet = inlineformset_factory(
    Transaccion,
    TransaccionDetail,
    form=TransaccionDetailForm,
    extra=3,
    can_delete=True,
)