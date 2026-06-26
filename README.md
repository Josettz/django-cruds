# Sales_A2 — Sistema de Ventas y Facturación (Django)

Proyecto replicado de la guía `Guia_Django_Ventas`. Incluye Partes 1–12:
modelos, admin, auth, CRUD (FBV + CBV), carpeta `shared/`
(mixin staff, decorador de auditoría, validador de cédula EC),
home/dashboard, logout POST y factura con formset.

## Estructura

```
Sales_A2/
├── config/          # Proyecto Django (settings, urls, wsgi/asgi)
├── billing/         # App principal (models, views, forms, urls, admin, templates)
├── shared/          # Código reutilizable (mixins, decorators, validators) — NO es app
├── templates/registration/  # login.html, signup.html
├── manage.py
└── requirements.txt
```

## Puesta en marcha (Windows)

```bash
cd Sales_A2
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abrir http://127.0.0.1:8000/ (requiere login) — admin en /admin/.

## Notas
- El campo `Customer.dni` valida cédula/RUC ecuatoriano (`shared/validators.py`).
- Borrar (Delete) en grupos, proveedores, productos y clientes requiere usuario **staff**.
- Las vistas de Brand registran auditoría en consola (`@audit_action`).
- La factura calcula IVA 15% y total al crear (formset de detalles).

## Listado de Productos — búsqueda y paginación

`ProductListView` (`billing/views.py`) soporta filtros por columna y paginado
(10 por página). Los filtros se conservan al cambiar de página vía querystring.

| Columna | Parámetro GET | Control en plantilla |
|---------|---------------|----------------------|
| Name | `name` | input texto (`icontains`) |
| Brand | `brand` | select (FK id) |
| Group | `group` | select (FK id) |
| Supplier | `supplier` | select (M2M id) |
| Price | `price_min` / `price_max` | input número (rango `gte`/`lte`) |
| Stock | `stock_min` / `stock_max` | input número (rango `gte`/`lte`) |
| Active | `is_active` | select (`1`=activo, `0`=inactivo) |

Ejemplo: `/products/?name=mouse&brand=2&price_min=10&is_active=1&page=2`

### Exportar a PDF / Excel

Botones **Export PDF** y **Export Excel** en el listado. Exportan el queryset
**ya filtrado** (los filtros viajan en la misma querystring):

- `?export=pdf` → PDF (reportlab)
- `?export=excel` → Excel `.xlsx` (openpyxl)

Implementado con el mixin genérico `ExportListMixin` (`shared/mixins.py`),
reutilizable en cualquier `ListView`:

```python
class ProductListView(LoginRequiredMixin, ExportListMixin, ListView):
    export_filename = 'productos'
    export_title = 'Listado de Productos'
    export_fields = [
        ('Name', 'name'),                 # atributo
        ('Brand', 'brand.name'),          # ruta con puntos (FK)
        ('Suppliers', lambda o: ', '.join(s.name for s in o.suppliers.all())),  # callable (M2M)
    ]
```

Dependencias nuevas: `openpyxl`, `reportlab` (ver `requirements.txt`).

### Columnas dinámicas (tabla + exportaciones)

Botón **⚙ Campos visibles** abre un modal (checklist) para elegir qué columnas
mostrar. Botones: **Aplicar**, **Restablecer configuración**, **Seleccionar todo**.
Mínimo obligatorio: 1 columna. Contador "Mostrando X de Y columnas".

**Fuente única de columnas**: el atributo `ProductListView.COLUMNS`
(`billing/views.py`) define `key`, `label`, `accessor` y `default` de cada
columna. La tabla, el PDF y el Excel usan esa misma lista, así que siempre
muestran/exportan exactamente lo mismo.

- Persistencia: la selección se guarda en **sesión** (`product_visible_columns`),
  se mantiene al navegar/paginar y la leen también las exportaciones.
- PDF: orientación (vertical/horizontal), tamaño de fuente y ancho de columnas
  se ajustan automáticamente según cuántas columnas haya.
- Excel: ancho de columnas auto según contenido, encabezados con estilo.
- Productos sin imagen muestran un placeholder (`billing/static/billing/no-image.svg`).

Para reutilizar la exportación dinámica en otra `ListView`: sobreescribir
`get_export_fields()` para devolver `[(label, accessor), ...]` de las columnas
visibles (ver `ExportListMixin`).

## Formulario de Producto (`ProductForm`)

`ProductCreateView` y `ProductUpdateView` usan `ProductForm`
(`billing/forms.py`) — un `ModelForm` que centraliza widgets, estilos
Bootstrap, placeholders, help_text y mensajes de error (sin config en las vistas).

- **Validación `unit_price`**: `clean_unit_price()` exige numérico y > 0
  → *"El precio unitario debe ser mayor que cero."* En frontend: `min="0.01"`
  y validación inmediata (JS) sin recargar.
- **Diseño** (`product_form.html`): dos columnas responsive (Bootstrap cards
  con sombra). Izquierda = datos; derecha = imagen + resumen.
- **Vista previa de imagen**: al seleccionar archivo se muestra al instante
  (FileReader). En edición carga la imagen actual y permite reemplazarla.
- **Balance dinámico**: `Precio × Stock` se recalcula en vivo (JS) en un campo
  solo lectura con formato monetario.

### Propiedad `Product.balance`

```python
@property
def balance(self):
    return (self.unit_price * self.stock).quantize(Decimal('0.01'), ROUND_HALF_UP)
```

Calculada (no persistida). Disponible como columna **Balance** en el listado,
compatible con selección dinámica de columnas y exportación PDF/Excel.

## CRUD genérico reutilizable (Brand, ProductGroup, Supplier, Customer)

Las mismas mejoras de Product (filtros, paginación, export PDF/Excel, columnas
dinámicas, detalle y formularios profesionales) se replicaron a los demás
modelos mediante **mixins reutilizables** y **plantillas genéricas**, sin
duplicar lógica.

### Mixins (`shared/mixins.py`)

- `DynamicColumnsMixin` — selección de columnas vía `COLUMNS` (key/label/accessor/
  default), persistida en sesión; aporta `get_export_fields()` y contexto.
- `GenericFilterMixin` — filtros declarativos vía `filters`
  (`type`: `text` | `boolean`); aplica en `get_queryset` y renderiza el form.
- `ExportListMixin` — exportación PDF/Excel (ya existente).
- `ListFeaturesMixin` — combina los tres + genera filas/URLs para la plantilla
  genérica.
- `GenericDetailMixin` — detalle vía `detail_fields = [(label, accessor), ...]`.

### Plantillas genéricas

- `billing/_generic_list.html` — listado (filtros, export, modal de columnas, paginación).
- `billing/_generic_detail.html` — ficha de detalle.
- `billing/_generic_form.html` — formulario Bootstrap (auto-render de cualquier `ModelForm`).

### Cómo agregar otro modelo a este patrón

```python
class FooListView(LoginRequiredMixin, ListFeaturesMixin, ListView):
    model = Foo
    template_name = 'billing/_generic_list.html'
    paginate_by = 10
    export_filename = 'foos'; export_title = 'Listado de Foos'; page_title = 'Foos'
    list_url_name = 'billing:foo_list'; create_url_name = 'billing:foo_create'
    detail_url_name = 'billing:foo_detail'; update_url_name = 'billing:foo_update'
    delete_url_name = 'billing:foo_delete'
    COLUMNS = [{'key': 'name', 'label': 'Nombre', 'default': True, 'accessor': 'name'}]
    filters = [{'name': 'name', 'label': 'Nombre', 'type': 'text', 'field': 'name'}]
```

> Nota: **Brand** pasó de FBV a CBV (`BrandListView`, etc.). Se eliminó el
> logging `@audit_action` que tenía la versión FBV. Cada modelo tiene ahora ruta
> de detalle `…/<pk>/`. Las plantillas antiguas por modelo (`brand_list.html`,
> `supplier_form.html`, etc.) quedan en desuso.

## Módulo de Compras (app `purchasing`)

App nueva que documenta las **adquisiciones a proveedores**: a quién se compró,
qué productos, en qué cantidad y a qué costo, calculando subtotal, IVA (15%) y
total. Es el espejo del lado de ventas (`Invoice`/`InvoiceDetail` de `billing`),
con la diferencia de negocio: la venta **resta** stock y la compra lo **suma**.

### Reutilización de modelos entre apps

`purchasing` **no duplica** modelos: importa `Supplier` y `Product` desde
`billing` y los referencia con `ForeignKey`.

```python
# purchasing/models.py
from billing.models import Supplier, Product   # reutilización entre apps

class Purchase(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchases')
    document_number = models.CharField(max_length=20)   # factura física del proveedor
    # ... purchase_date, subtotal, tax, total, is_active

class PurchaseDetail(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='details')
    product  = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='purchase_details')
    quantity = models.PositiveIntegerField(default=1)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)   # COSTO, no precio de venta
```

- Una compra apunta **a los mismos** proveedores y productos que las ventas; no
  hay catálogos paralelos.
- `on_delete`: `PROTECT` en `supplier`/`product` (no se borran si tienen compras),
  `CASCADE` en el detalle (al borrar la compra caen sus líneas).
- `PurchaseDetail.save()` calcula el subtotal de la línea (`quantity * unit_cost`).
- Dinero siempre con `Decimal`.

### Mapa Ventas → Compras

| Ventas (`billing`) | Compras (`purchasing`) | Cambio clave |
|--------------------|------------------------|--------------|
| `Invoice` | `Purchase` | `customer` → `supplier`; se agrega `document_number` |
| `InvoiceDetail` | `PurchaseDetail` | `unit_price` → `unit_cost` |
| `billing:invoice_*` | `purchasing:purchase_*` | nuevo `app_name = 'purchasing'` |
| El stock NO cambia | El stock **SUMA** | la compra reabastece inventario |

### Rutas (`/purchases/`)

| URL | Vista (FBV) | Función |
|-----|-------------|---------|
| `/purchases/` | `purchase_list` | listado (`select_related('supplier')`) |
| `/purchases/create/` | `purchase_create` | alta con formset; calcula totales y **suma stock** |
| `/purchases/<pk>/` | `purchase_detail` | detalle (`prefetch_related('details__product')`) |
| `/purchases/<pk>/delete/` | `purchase_delete` | borra y **revierte stock** |

### Inventario (stock)

- **Al crear** una compra: `product.stock += quantity` por cada línea.
- **Al borrar** una compra: revierte (`stock -= quantity`), con validación previa
  *todo-o-nada* — si algún producto quedaría en negativo (ya se vendió), cancela
  la operación sin tocar nada y avisa al usuario.

### Formulario maestro–detalle

`PurchaseForm` (cabecera) + `PurchaseDetailFormSet`
(`inlineformset_factory`, `extra=3`, `can_delete=True`) permiten registrar varias
líneas en una sola compra. El template (`purchase_form.html`) calcula subtotal/
IVA/total en vivo (JS) y **autocompleta el costo** al elegir un producto: usa el
último `unit_cost` con que se compró (o el precio de venta como referencia si
nunca se compró), editable siempre.

### Admin

`PurchaseAdmin` registra `Purchase` con `PurchaseDetailInline` (`TabularInline`)
y `list_display = (id, supplier, document_number, purchase_date, total)`.

