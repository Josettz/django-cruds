from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import inlineformset_factory

from .models import Brand, ProductGroup, Supplier, Customer, Invoice, InvoiceDetail, Product


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields:
            self.fields[f].widget.attrs['class'] = 'form-control'


class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'description', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Logitech', 'autofocus': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción de la marca...'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {'name': 'Nombre de la marca (único).'}
        error_messages = {'name': {'required': 'El nombre de la marca es obligatorio.',
                                   'unique': 'Ya existe una marca con ese nombre.'}}


class ProductGroupForm(forms.ModelForm):
    class Meta:
        model = ProductGroup
        fields = ['name', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Periféricos', 'autofocus': True}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {'name': 'Nombre de la categoría (único).'}
        error_messages = {'name': {'required': 'El nombre de la categoría es obligatorio.',
                                   'unique': 'Ya existe una categoría con ese nombre.'}}


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_name', 'email', 'phone', 'address', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Empresa S.A.', 'autofocus': True}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de contacto'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@empresa.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09xxxxxxxx'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Dirección...'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {'name': 'Razón social del proveedor.', 'email': 'Correo de contacto (opcional).'}
        error_messages = {'name': {'required': 'El nombre del proveedor es obligatorio.'}}


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['dni', 'first_name', 'last_name', 'email', 'phone', 'address', 'is_active']
        widgets = {
            'dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cédula / RUC', 'autofocus': True}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@dominio.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09xxxxxxxx'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Dirección...'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {'dni': 'Cédula o RUC ecuatoriano válido.'}
        error_messages = {
            'dni': {'required': 'El DNI/RUC es obligatorio.', 'unique': 'Ya existe un cliente con ese DNI/RUC.'},
            'first_name': {'required': 'El nombre es obligatorio.'},
            'last_name': {'required': 'El apellido es obligatorio.'},
        }


class ProductForm(forms.ModelForm):
    """
    Formulario centralizado de Producto (Create + Update).
    Centraliza widgets, estilos Bootstrap, placeholders, help_text,
    mensajes de error y validación de unit_price.
    """

    class Meta:
        model = Product
        fields = ['name', 'description', 'brand', 'group', 'suppliers',
                  'image', 'unit_price', 'stock', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Teclado mecánico RGB',
                'autofocus': True,
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción breve del producto...',
            }),
            'brand': forms.Select(attrs={'class': 'form-select'}),
            'group': forms.Select(attrs={'class': 'form-select'}),
            'suppliers': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 4}),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'id_image',
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00',
                'id': 'id_unit_price',
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1',
                'placeholder': '0',
                'id': 'id_stock',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'name': 'Nombre comercial del producto.',
            'brand': 'Marca a la que pertenece.',
            'group': 'Categoría / grupo del producto.',
            'suppliers': 'Mantén Ctrl para seleccionar varios.',
            'image': 'Formatos de imagen. Opcional.',
            'unit_price': 'Valor mayor que cero. Ej: 10.50',
            'stock': 'Cantidad disponible en inventario.',
        }
        error_messages = {
            'name': {'required': 'El nombre del producto es obligatorio.'},
            'brand': {'required': 'Selecciona una marca.'},
            'group': {'required': 'Selecciona una categoría.'},
            'unit_price': {
                'required': 'El precio unitario es obligatorio.',
                'invalid': 'Ingresa un valor numérico válido.',
            },
            'stock': {'invalid': 'El stock debe ser un número entero.'},
        }

    def clean_unit_price(self):
        "Valida que el precio unitario sea mnayor a cero"
        price = self.cleaned_data.get('unit_price')
        if price is not None and price <= 0:
            raise forms.ValidationError(
            'El precio unitario debe ser mayor que cero.'
        )
        return price

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock is not None and stock < 0:
            raise forms.ValidationError('El stock no puede ser negativo.')
        return stock


class InvoiceForm(forms.ModelForm):
    """Formulario para cabecera de factura."""
    class Meta:
        model = Invoice
        fields = ['customer']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
        }


class InvoiceDetailForm(forms.ModelForm):
    """Línea de factura. Quita el initial del campo quantity para que las
    filas vacías NO se consideren obligatorias (permite facturas con 1 solo
    producto sin tener que llenar las demás filas)."""
    class Meta:
        model = InvoiceDetail
        fields = ['product', 'quantity', 'unit_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El default=1 del modelo se propaga como initial y marcaba las filas
        # vacías como "cambiadas", forzando su validación. Lo limpiamos.
        self.fields['quantity'].initial = None


# Formset: permite agregar MÚLTIPLES detalles dentro de UNA factura
InvoiceDetailFormSet = inlineformset_factory(
    Invoice,           # Modelo padre
    InvoiceDetail,     # Modelo hijo
    form=InvoiceDetailForm,
    extra=3,           # 3 filas vacías para agregar
    can_delete=True,   # Checkbox para eliminar filas
)
