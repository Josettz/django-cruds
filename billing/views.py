import json
from decimal import Decimal

from django.utils import timezone
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth import login

from .models import Brand, ProductGroup, Supplier, Product, Customer, Invoice
from .forms import (
    SignUpForm, BrandForm, ProductGroupForm, SupplierForm, CustomerForm,
    ProductForm, InvoiceForm, InvoiceDetailFormSet,
)
from shared.mixins import (
    StaffRequiredMixin, ExportListMixin, DynamicColumnsMixin,
    ListFeaturesMixin, GenericDetailMixin,
)
from shared.decorators import audit_action
from shared.exports import export_excel, export_pdf
from shared.columns import columns_context, get_visible_columns, visible_export
from shared.money import compute_totals


# === Columnas dinámicas de Facturas (tabla + PDF + Excel) ===
INVOICE_COLUMNS = [
    {'key': 'id',        'label': '#',        'default': True,  'accessor': 'id'},
    {'key': 'customer',  'label': 'Cliente',  'default': True,  'accessor': lambda o: str(o.customer)},
    {'key': 'date',      'label': 'Fecha',    'default': True,  'accessor': lambda o: o.invoice_date.strftime('%d/%m/%Y')},
    {'key': 'subtotal',  'label': 'Subtotal', 'default': True,  'accessor': 'subtotal'},
    {'key': 'tax',       'label': 'IVA',      'default': True,  'accessor': 'tax'},
    {'key': 'total',     'label': 'Total',    'default': True,  'accessor': 'total'},
    {'key': 'is_active', 'label': 'Activo',   'default': False, 'accessor': lambda o: 'Sí' if o.is_active else 'No'},
]


# === HOME (Página principal) ===
@login_required
def home(request):
    """Vista principal del sistema. Muestra resumen general."""
    context = {
        'total_brands': Brand.objects.count(),
        'total_products': Product.objects.count(),
        'total_customers': Customer.objects.count(),
        'total_invoices': Invoice.objects.count(),
        'recent_invoices': Invoice.objects.all()[:5],
        'low_stock': Product.objects.filter(stock__lte=5, is_active=True),
    }
    return render(request, 'billing/home.html', context)


# === REGISTRO ===
class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('billing:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


# Helpers reutilizables para accessors comunes
def _yesno(o):
    return 'Sí' if o.is_active else 'No'

def _dt(field):
    return lambda o: getattr(o, field).strftime('%d/%m/%Y %H:%M') if getattr(o, field) else ''

def _img_url(o):
    """URL de la imagen (texto plano) -> sirve para tabla y exportaciones."""
    return o.image.url if o.image else ''

def _img_detail(o):
    """Miniatura HTML segura para la vista de detalle.
    Sin imagen -> placeholder no-image.svg, igual que en productos."""
    from django.utils.safestring import mark_safe
    from django.utils.html import escape
    from django.templatetags.static import static
    src = escape(o.image.url) if o.image else static('billing/no-image.svg')
    return mark_safe(
        f'<img src="{src}" class="img-thumbnail" '
        f'style="max-width:160px;max-height:160px;object-fit:cover;" alt="">'
    )


# === BRAND (CBV) ===
class BrandListView(LoginRequiredMixin, ListFeaturesMixin, ListView):
    model = Brand
    template_name = 'billing/_generic_list.html'
    paginate_by = 3
    export_filename = 'marcas'
    export_title = 'Listado de Marcas'
    page_title = 'Marcas'
    list_url_name = 'billing:brand_list'
    create_url_name = 'billing:brand_create'
    detail_url_name = 'billing:brand_detail'
    update_url_name = 'billing:brand_update'
    delete_url_name = 'billing:brand_delete'
    COLUMNS = [
        {'key': 'image',       'label': 'Imagen',         'default': True,  'accessor': _img_url, 'image': True},
        {'key': 'name',        'label': 'Nombre',         'default': True,  'accessor': 'name'},
        {'key': 'description', 'label': 'Descripción',    'default': True,  'accessor': 'description'},
        {'key': 'is_active',   'label': 'Activo',         'default': True,  'accessor': _yesno, 'boolean': True},
        {'key': 'created_at',  'label': 'Fecha creación', 'default': False, 'accessor': _dt('created_at')},
    ]
    filters = [
        {'name': 'name', 'label': 'Nombre', 'type': 'text', 'field': 'name'},
        {'name': 'is_active', 'label': 'Activo', 'type': 'boolean'},
    ]


class BrandDetailView(LoginRequiredMixin, GenericDetailMixin, DetailView):
    model = Brand
    template_name = 'billing/_generic_detail.html'
    page_title = 'Detalle de Marca'
    list_url_name = 'billing:brand_list'
    update_url_name = 'billing:brand_update'
    delete_url_name = 'billing:brand_delete'
    detail_fields = [
        ('Imagen', _img_detail), ('Nombre', 'name'), ('Descripción', 'description'), ('Activo', _yesno),
        ('Creado', _dt('created_at')), ('Actualizado', _dt('updated_at')),
    ]


class BrandCreateView(LoginRequiredMixin, CreateView):
    model = Brand
    form_class = BrandForm
    template_name = 'billing/_generic_form.html'
    success_url = reverse_lazy('billing:brand_list')
    extra_context = {'page_title': 'Nueva Marca', 'list_url': reverse_lazy('billing:brand_list')}


class BrandUpdateView(LoginRequiredMixin, UpdateView):
    model = Brand
    form_class = BrandForm
    template_name = 'billing/_generic_form.html'
    success_url = reverse_lazy('billing:brand_list')
    extra_context = {'page_title': 'Editar Marca', 'list_url': reverse_lazy('billing:brand_list')}


class BrandDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Brand
    template_name = 'billing/brand_confirm_delete.html'
    success_url = reverse_lazy('billing:brand_list')
    staff_redirect_url = '/brands/'


# === PRODUCTGROUP (CBV) ===
class ProductGroupListView(LoginRequiredMixin, ListFeaturesMixin, ListView):
    model = ProductGroup
    template_name = 'billing/_generic_list.html'
    paginate_by = 3
    export_filename = 'categorias'
    export_title = 'Listado de Categorías'
    page_title = 'Categorías'
    list_url_name = 'billing:productgroup_list'
    create_url_name = 'billing:productgroup_create'
    detail_url_name = 'billing:productgroup_detail'
    update_url_name = 'billing:productgroup_update'
    delete_url_name = 'billing:productgroup_delete'
    COLUMNS = [
        {'key': 'image',      'label': 'Imagen',         'default': True,  'accessor': _img_url, 'image': True},
        {'key': 'name',       'label': 'Nombre',         'default': True,  'accessor': 'name'},
        {'key': 'is_active',  'label': 'Activo',         'default': True,  'accessor': _yesno, 'boolean': True},
        {'key': 'created_at', 'label': 'Fecha creación', 'default': False, 'accessor': _dt('created_at')},
    ]
    filters = [
        {'name': 'name', 'label': 'Nombre', 'type': 'text', 'field': 'name'},
        {'name': 'is_active', 'label': 'Activo', 'type': 'boolean'},
    ]


class ProductGroupDetailView(LoginRequiredMixin, GenericDetailMixin, DetailView):
    model = ProductGroup
    template_name = 'billing/_generic_detail.html'
    page_title = 'Detalle de Categoría'
    list_url_name = 'billing:productgroup_list'
    update_url_name = 'billing:productgroup_update'
    delete_url_name = 'billing:productgroup_delete'
    detail_fields = [
        ('Imagen', _img_detail), ('Nombre', 'name'), ('Activo', _yesno),
        ('Creado', _dt('created_at')), ('Actualizado', _dt('updated_at')),
    ]


class ProductGroupCreateView(LoginRequiredMixin, CreateView):
    model = ProductGroup
    form_class = ProductGroupForm
    template_name = 'billing/_generic_form.html'
    success_url = reverse_lazy('billing:productgroup_list')
    extra_context = {'page_title': 'Nueva Categoría', 'list_url': reverse_lazy('billing:productgroup_list')}


class ProductGroupUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductGroup
    form_class = ProductGroupForm
    template_name = 'billing/_generic_form.html'
    success_url = reverse_lazy('billing:productgroup_list')
    extra_context = {'page_title': 'Editar Categoría', 'list_url': reverse_lazy('billing:productgroup_list')}


class ProductGroupDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = ProductGroup
    template_name = 'billing/productgroup_confirm_delete.html'
    success_url = reverse_lazy('billing:productgroup_list')
    staff_redirect_url = '/groups/'


# === SUPPLIER (CBV) ===
class SupplierListView(LoginRequiredMixin, ListFeaturesMixin, ListView):
    model = Supplier
    template_name = 'billing/_generic_list.html'
    paginate_by = 3
    export_filename = 'proveedores'
    export_title = 'Listado de Proveedores'
    page_title = 'Proveedores'
    list_url_name = 'billing:supplier_list'
    create_url_name = 'billing:supplier_create'
    detail_url_name = 'billing:supplier_detail'
    update_url_name = 'billing:supplier_update'
    delete_url_name = 'billing:supplier_delete'
    COLUMNS = [
        {'key': 'image',        'label': 'Imagen',         'default': True,  'accessor': _img_url, 'image': True},
        {'key': 'name',         'label': 'Empresa',        'default': True,  'accessor': 'name'},
        {'key': 'contact_name', 'label': 'Contacto',       'default': True,  'accessor': 'contact_name'},
        {'key': 'email',        'label': 'Email',          'default': True,  'accessor': 'email'},
        {'key': 'phone',        'label': 'Teléfono',       'default': True,  'accessor': 'phone'},
        {'key': 'address',      'label': 'Dirección',      'default': False, 'accessor': 'address'},
        {'key': 'is_active',    'label': 'Activo',         'default': True,  'accessor': _yesno, 'boolean': True},
        {'key': 'created_at',   'label': 'Fecha creación', 'default': False, 'accessor': _dt('created_at')},
    ]
    filters = [
        {'name': 'name', 'label': 'Empresa', 'type': 'text', 'field': 'name'},
        {'name': 'contact_name', 'label': 'Contacto', 'type': 'text', 'field': 'contact_name'},
        {'name': 'email', 'label': 'Email', 'type': 'text', 'field': 'email'},
        {'name': 'is_active', 'label': 'Activo', 'type': 'boolean'},
    ]


class SupplierDetailView(LoginRequiredMixin, GenericDetailMixin, DetailView):
    model = Supplier
    template_name = 'billing/_generic_detail.html'
    page_title = 'Detalle de Proveedor'
    list_url_name = 'billing:supplier_list'
    update_url_name = 'billing:supplier_update'
    delete_url_name = 'billing:supplier_delete'
    detail_fields = [
        ('Imagen', _img_detail), ('Empresa', 'name'), ('Contacto', 'contact_name'), ('Email', 'email'),
        ('Teléfono', 'phone'), ('Dirección', 'address'), ('Activo', _yesno),
        ('Creado', _dt('created_at')), ('Actualizado', _dt('updated_at')),
    ]


class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'billing/_generic_form.html'
    success_url = reverse_lazy('billing:supplier_list')
    extra_context = {'page_title': 'Nuevo Proveedor', 'list_url': reverse_lazy('billing:supplier_list')}


class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'billing/_generic_form.html'
    success_url = reverse_lazy('billing:supplier_list')
    extra_context = {'page_title': 'Editar Proveedor', 'list_url': reverse_lazy('billing:supplier_list')}


class SupplierDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Supplier
    template_name = 'billing/supplier_confirm_delete.html'
    success_url = reverse_lazy('billing:supplier_list')
    staff_redirect_url = '/suppliers/'


# === PRODUCT (CBV) ===
class ProductListView(LoginRequiredMixin, DynamicColumnsMixin, ExportListMixin, ListView):
    model = Product
    template_name = 'billing/product_list.html'
    context_object_name = 'items'
    paginate_by = 3

    export_filename = 'productos'
    export_title = 'Listado de Productos'
    columns_session_key = 'product_visible_columns'

    # === FUENTE ÚNICA DE COLUMNAS (tabla + PDF + Excel) ===
    # key      -> usado por la plantilla y para guardar la selección
    # label    -> encabezado mostrado y exportado
    # accessor -> str | "a.b" | callable(obj) usado en exportaciones
    # default  -> visible por defecto
    COLUMNS = [
        {'key': 'image',       'label': 'Imagen',         'default': True,
         'accessor': lambda o: o.image.url if o.image else 'Sin imagen'},
        {'key': 'name',        'label': 'Nombre',         'default': True,  'accessor': 'name'},
        {'key': 'description', 'label': 'Descripción',    'default': False, 'accessor': 'description'},
        {'key': 'brand',       'label': 'Marca',          'default': True,  'accessor': 'brand.name'},
        {'key': 'group',       'label': 'Categoría',      'default': True,  'accessor': 'group.name'},
        {'key': 'price',       'label': 'Precio',         'default': True,  'accessor': 'unit_price'},
        {'key': 'stock',       'label': 'Stock',          'default': False, 'accessor': 'stock'},
        {'key': 'balance',     'label': 'Balance',        'default': False,
         'accessor': lambda o: f'{o.balance:.2f}'},
        {'key': 'suppliers',   'label': 'Proveedores',    'default': True,
         'accessor': lambda o: ', '.join(s.name for s in o.suppliers.all()) or 'Ninguno'},
        {'key': 'is_active',   'label': 'Activo',         'default': True,
         'accessor': lambda o: 'Sí' if o.is_active else 'No'},
        {'key': 'created_at',  'label': 'Fecha creación', 'default': False,
         'accessor': lambda o: o.created_at.strftime('%d/%m/%Y %H:%M')},
    ]
    def get_queryset(self):
        qs = super().get_queryset().select_related('brand', 'group').prefetch_related('suppliers')
        p = self.request.GET

        name = p.get('name', '').strip()
        if name:
            qs = qs.filter(name__icontains=name)

        brand = p.get('brand', '').strip()
        if brand:
            qs = qs.filter(brand_id=brand)

        group = p.get('group', '').strip()
        if group:
            qs = qs.filter(group_id=group)

        supplier = p.get('supplier', '').strip()
        if supplier:
            qs = qs.filter(suppliers__id=supplier)

        price_min = p.get('price_min', '').strip()
        if price_min:
            qs = qs.filter(unit_price__gte=price_min)

        price_max = p.get('price_max', '').strip()
        if price_max:
            qs = qs.filter(unit_price__lte=price_max)

        stock_min = p.get('stock_min', '').strip()
        if stock_min:
            qs = qs.filter(stock__gte=stock_min)

        stock_max = p.get('stock_max', '').strip()
        if stock_max:
            qs = qs.filter(stock__lte=stock_max)

        is_active = p.get('is_active', '').strip()
        if is_active in ('0', '1'):
            qs = qs.filter(is_active=(is_active == '1'))

        return qs.distinct()

    def get_context_data(self, **kwargs):
        # columnas dinámicas + querystring/filters -> los aporta DynamicColumnsMixin
        ctx = super().get_context_data(**kwargs)
        ctx['brands'] = Brand.objects.all()
        ctx['groups'] = ProductGroup.objects.all()
        ctx['suppliers'] = Supplier.objects.all()
        return ctx


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'billing/product_detail.html'
    context_object_name = 'product'


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'billing/product_form.html'
    success_url = reverse_lazy('billing:product_list')


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'billing/product_form.html'
    success_url = reverse_lazy('billing:product_list')


class ProductDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Product 
    template_name = 'billing/product_confirm_delete.html'
    success_url = reverse_lazy('billing:product_list')
    staff_redirect_url = '/products/'


# === CUSTOMER (CBV) ===
class CustomerListView(LoginRequiredMixin, ListFeaturesMixin, ListView):
    model = Customer
    template_name = 'billing/_generic_list.html'
    paginate_by = 10
    export_filename = 'clientes'
    export_title = 'Listado de Clientes'
    page_title = 'Clientes'
    list_url_name = 'billing:customer_list'
    create_url_name = 'billing:customer_create'
    detail_url_name = 'billing:customer_detail'
    update_url_name = 'billing:customer_update'
    delete_url_name = 'billing:customer_delete'
    COLUMNS = [
        {'key': 'dni',        'label': 'DNI / RUC',      'default': True,  'accessor': 'dni'},
        {'key': 'first_name', 'label': 'Nombres',        'default': True,  'accessor': 'first_name'},
        {'key': 'last_name',  'label': 'Apellidos',      'default': True,  'accessor': 'last_name'},
        {'key': 'email',      'label': 'Email',          'default': True,  'accessor': 'email'},
        {'key': 'phone',      'label': 'Teléfono',       'default': True,  'accessor': 'phone'},
        {'key': 'address',    'label': 'Dirección',      'default': False, 'accessor': 'address'},
        {'key': 'is_active',  'label': 'Activo',         'default': True,  'accessor': _yesno, 'boolean': True},
        {'key': 'created_at', 'label': 'Fecha creación', 'default': False, 'accessor': _dt('created_at')},
    ]
    filters = [
        {'name': 'dni', 'label': 'DNI / RUC', 'type': 'text', 'field': 'dni'},
        {'name': 'first_name', 'label': 'Nombres', 'type': 'text', 'field': 'first_name'},
        {'name': 'last_name', 'label': 'Apellidos', 'type': 'text', 'field': 'last_name'},
        {'name': 'email', 'label': 'Email', 'type': 'text', 'field': 'email'},
        {'name': 'is_active', 'label': 'Activo', 'type': 'boolean'},
    ]


class CustomerDetailView(LoginRequiredMixin, GenericDetailMixin, DetailView):
    model = Customer
    template_name = 'billing/_generic_detail.html'
    page_title = 'Detalle de Cliente'
    list_url_name = 'billing:customer_list'
    update_url_name = 'billing:customer_update'
    delete_url_name = 'billing:customer_delete'
    detail_fields = [
        ('DNI / RUC', 'dni'), ('Nombres', 'first_name'), ('Apellidos', 'last_name'),
        ('Email', 'email'), ('Teléfono', 'phone'), ('Dirección', 'address'),
        ('Activo', _yesno), ('Creado', _dt('created_at')), ('Actualizado', _dt('updated_at')),
    ]


class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'billing/_generic_form.html'
    success_url = reverse_lazy('billing:customer_list')
    extra_context = {'page_title': 'Nuevo Cliente', 'list_url': reverse_lazy('billing:customer_list')}


class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'billing/_generic_form.html'
    success_url = reverse_lazy('billing:customer_list')
    extra_context = {'page_title': 'Editar Cliente', 'list_url': reverse_lazy('billing:customer_list')}


class CustomerDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Customer
    template_name = 'billing/customer_confirm_delete.html'
    success_url = reverse_lazy('billing:customer_list')
    staff_redirect_url = '/customers/'


# =============================================
# CRUD DE INVOICE - VISTAS BASADAS EN FUNCIONES
# (Requiere FBV porque usa formsets complejos)
# =============================================

@login_required
def invoice_list(request):
    """Lista facturas con filtros y paginación (igual que productos)."""
    qs = Invoice.objects.select_related('customer').all()
    p = request.GET

    customer = p.get('customer', '').strip()
    if customer:
        qs = qs.filter(customer_id=customer)

    date_from = p.get('date_from', '').strip()
    if date_from:
        qs = qs.filter(invoice_date__date__gte=date_from)

    date_to = p.get('date_to', '').strip()
    if date_to:
        qs = qs.filter(invoice_date__date__lte=date_to)

    total_min = p.get('total_min', '').strip()
    if total_min:
        qs = qs.filter(total__gte=total_min)

    total_max = p.get('total_max', '').strip()
    if total_max:
        qs = qs.filter(total__lte=total_max)

    is_active = p.get('is_active', '').strip()
    if is_active in ('0', '1'):
        qs = qs.filter(is_active=(is_active == '1'))

    # Exportar (respeta filtros y columnas visibles). Botones PDF/Excel.
    export = p.get('export')
    if export in ('excel', 'pdf'):
        visible = get_visible_columns(request, INVOICE_COLUMNS, 'invoice_visible_columns')
        headers, rows = visible_export(INVOICE_COLUMNS, visible, qs)
        fn = export_excel if export == 'excel' else export_pdf
        return fn(headers, rows, 'facturas', 'Listado de Facturas')

    paginator = Paginator(qs, 3)
    page_obj = paginator.get_page(p.get('page'))

    params = request.GET.copy()
    for k in ('page', 'columns', 'reset_columns'):
        params.pop(k, None)

    ctx = {
        'items': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'querystring': params.urlencode(),
        'filters': request.GET,
        'customers': Customer.objects.all(),
    }
    ctx.update(columns_context(request, INVOICE_COLUMNS, 'invoice_visible_columns'))
    return render(request, 'billing/invoice_list.html', ctx)


@login_required
def invoice_create(request):
    """Crea factura con sus líneas de detalle."""
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        formset = InvoiceDetailFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            # Una factura debe tener al menos una línea con producto; sin esto
            # se podría crear una factura vacía (sin nada).
            has_detail = any(
                f.cleaned_data.get('product') and not f.cleaned_data.get('DELETE')
                for f in formset.forms
            )
            if not has_detail:
                messages.error(request, 'Debes agregar al menos un producto a la factura.')
            else:
                # Cantidad pedida por producto (sumando líneas repetidas)
                needed = {}
                for f in formset.forms:
                    cd = f.cleaned_data
                    if not cd or cd.get('DELETE'):
                        continue
                    p = cd.get('product')
                    if not p:
                        continue
                    needed[p.id] = needed.get(p.id, 0) + cd.get('quantity', 0)

                # Validar stock disponible ANTES de crear nada
                faltante = None
                for pid, qty in needed.items():
                    prod = Product.objects.get(pk=pid)
                    if prod.stock < qty:
                        faltante = prod
                        break

                if faltante is not None:
                    messages.error(
                        request,
                        f'Stock insuficiente para "{faltante.name}": '
                        f'hay {faltante.stock} y se piden {needed[faltante.id]}.'
                    )
                else:
                    invoice = form.save(commit=False)
                    invoice.save()

                    formset.instance = invoice
                    formset.save()

                    # Descontar stock vendido
                    for pid, qty in needed.items():
                        prod = Product.objects.get(pk=pid)
                        prod.stock -= qty
                        prod.save(update_fields=['stock'])

                    subtotal = sum((d.subtotal for d in invoice.details.all()), Decimal('0'))
                    invoice.subtotal, invoice.tax, invoice.total = compute_totals(subtotal)
                    invoice.save()

                    messages.success(request, f'¡Factura #{invoice.id} creada! Total: ${invoice.total}')
                    return redirect('billing:invoice_list')
    else:
        form = InvoiceForm()
        formset = InvoiceDetailFormSet()

    # Mapa de precios para autocompletar Unit Price al elegir producto (JS)
    product_prices = {
        str(p.id): str(p.unit_price)
        for p in Product.objects.filter(is_active=True)
    }

    return render(request, 'billing/invoice_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Crear Factura',
        'product_prices_json': json.dumps(product_prices),
        'today': timezone.localdate(),
    })


@login_required
def invoice_update(request, pk):
    """Edita una factura; ajusta el stock por la DIFERENCIA de cantidades vendidas."""
    invoice = get_object_or_404(
        Invoice.objects.prefetch_related('details__product'), pk=pk
    )

    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        formset = InvoiceDetailFormSet(request.POST, instance=invoice)

        if form.is_valid() and formset.is_valid():
            # Igual que al crear: la factura no puede quedar sin líneas.
            has_detail = any(
                f.cleaned_data.get('product') and not f.cleaned_data.get('DELETE')
                for f in formset.forms
            )
            if not has_detail:
                messages.error(request, 'Debes agregar al menos un producto a la factura.')
            else:
                # Cantidades actuales (lo que esta factura YA restó del stock)
                old_qty = {}
                for d in invoice.details.all():
                    old_qty[d.product_id] = old_qty.get(d.product_id, 0) + d.quantity

                # Cantidades nuevas según el formulario
                new_qty = {}
                for f in formset.forms:
                    cd = f.cleaned_data
                    if not cd or cd.get('DELETE'):
                        continue
                    p = cd.get('product')
                    if not p:
                        continue
                    new_qty[p.id] = new_qty.get(p.id, 0) + cd.get('quantity', 0)

                # Validar ANTES de guardar: una venta solo puede restar lo que hay.
                # nuevo_stock = stock_actual + vendido_antes - vendido_ahora
                faltante = None
                for pid in set(old_qty) | set(new_qty):
                    delta = new_qty.get(pid, 0) - old_qty.get(pid, 0)
                    prod = Product.objects.get(pk=pid)
                    if prod.stock - delta < 0:
                        faltante = prod
                        break

                if faltante is not None:
                    messages.error(
                        request,
                        f'Stock insuficiente para "{faltante.name}": '
                        f'solo hay {faltante.stock} disponible(s).'
                    )
                else:
                    invoice = form.save()
                    formset.instance = invoice
                    formset.save()

                    # Aplicar el delta al stock (venta = resta)
                    for pid in set(old_qty) | set(new_qty):
                        delta = new_qty.get(pid, 0) - old_qty.get(pid, 0)
                        if delta:
                            prod = Product.objects.get(pk=pid)
                            prod.stock -= delta
                            prod.save(update_fields=['stock'])

                    subtotal = sum((d.subtotal for d in invoice.details.all()), Decimal('0'))
                    invoice.subtotal, invoice.tax, invoice.total = compute_totals(subtotal)
                    invoice.save()

                    messages.success(request, f'¡Factura #{invoice.id} actualizada! Total: ${invoice.total}')
                    return redirect('billing:invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm(instance=invoice)
        formset = InvoiceDetailFormSet(instance=invoice)

    product_prices = {
        str(p.id): str(p.unit_price)
        for p in Product.objects.filter(is_active=True)
    }

    return render(request, 'billing/invoice_form.html', {
        'form': form,
        'formset': formset,
        'title': f'Editar Factura #{invoice.id}',
        'product_prices_json': json.dumps(product_prices),
        'today': invoice.invoice_date,
        'is_edit': True,
        'object': invoice,
    })


@login_required
def invoice_detail(request, pk):
    """Muestra el detalle completo de una factura."""
    invoice = get_object_or_404(
        Invoice.objects.select_related('customer')
                       .prefetch_related('details__product'),
        pk=pk
    )
    return render(request, 'billing/invoice_detail.html', {'invoice': invoice})


@login_required
def invoice_delete(request, pk):
    """Elimina una factura y sus detalles (CASCADE); DEVUELVE el stock vendido."""
    invoice = get_object_or_404(
        Invoice.objects.prefetch_related('details__product'), pk=pk
    )
    if request.method == 'POST':
        invoice_id = invoice.id
        # Reponer el stock que esta factura había restado
        for detail in invoice.details.all():
            product = detail.product
            product.stock += detail.quantity
            product.save(update_fields=['stock'])

        invoice.delete()
        messages.success(request, f'¡Factura #{invoice_id} eliminada! Stock repuesto.')
        return redirect('billing:invoice_list')
    return render(request, 'billing/invoice_confirm_delete.html', {'object': invoice})
