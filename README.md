# Sales_A2 — Sistema de Ventas y Facturación

Proyecto Django 6.0 para gestión de ventas, compras, inventario, empleados y
transacciones financieras, desarrollado como parte de la materia de Software.

## Autores

**Software A2** — Universidad Estatal de Milagro (UNEMI), Ingeniería en Software, 4to semestre.

- José Antonio Torres Torres
---

## Estructura del proyecto

```
sales_a2_software/
├── config/                  # Configuración Django (settings, urls, wsgi/asgi)
├── billing/                 # App principal: Brand, ProductGroup, Supplier,
│                            #   Product, Customer, CustomerProfile, Invoice
├── purchasing/              # Compras: Purchase, PurchaseDetail
├── transaccion/             # Transacciones financieras + Seguridad
│   └── security/            #   Gestión de usuarios, roles y permisos
├── empleados/               # Empleados
├── tareas/                  # Tareas asignadas a empleados
├── shared/                  # Código reutilizable (mixins, validadores, etc.)
├── templates/registration/  # login.html, signup.html
├── media/                   # Imágenes subidas
├── db.sqlite3
├── manage.py
└── requirements.txt
```

## Puesta en marcha

```bash
cd sales_a2_software
python -m venv venv
source venv/bin/activate       # Linux/Mac
# venv\Scripts\activate        # Windows
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abrir http://127.0.0.1:8000/ — Admin en /admin/.

### Datos de prueba

```bash
python manage.py seed           # Crea marcas, grupos, proveedores, productos y clientes
python manage.py setup_roles    # Crea roles: Administrador, Vendedor, Analista de Compras
```

---

## Apps y modelos

### `billing` — Catálogo y ventas

| Modelo | Descripción | FK / Relaciones |
|--------|-------------|-----------------|
| `Brand` | Marcas de productos | — |
| `ProductGroup` | Categorías de productos | — |
| `Supplier` | Proveedores | M2M → `Product` |
| `Product` | Productos | FK → `Brand`, FK → `ProductGroup`, M2M → `Supplier` |
| `Customer` | Clientes (cédula/RUC ecuatoriano) | OneToOne → `CustomerProfile` |
| `CustomerProfile` | Perfil extendido del cliente | OneToOne → `Customer` |
| `Invoice` | Factura (cabecera) | FK → `Customer` |
| `InvoiceDetail` | Líneas de factura | FK → `Invoice`, FK → `Product` |

### `purchasing` — Compras

| Modelo | Descripción | FK / Relaciones |
|--------|-------------|-----------------|
| `Purchase` | Compra a proveedor | FK → `billing.Supplier` |
| `PurchaseDetail` | Líneas de compra | FK → `Purchase`, FK → `billing.Product` |

**Regla de negocio:** La compra **suma stock**, la venta lo resta.

### `transaccion` — Transacciones financieras

| Modelo | Descripción | FK / Relaciones |
|--------|-------------|-----------------|
| `Transaccion` | Ingreso/Egreso | FK → `billing.Invoice` (nullable), FK → `purchasing.Purchase` (nullable) |
| `TransaccionDetail` | Productos de la transacción | FK → `Transaccion`, FK → `billing.Product` |

Generación automática mediante señales (`signals.py`):
- Al crear/actualizar una `Purchase` → se crea/actualiza una `Transaccion` (tipo=egreso).
- Al crear/actualizar una `Invoice` → se crea/actualiza una `Transaccion` (tipo=ingreso).

### `empleados` — Empleados

| Modelo | Descripción |
|--------|-------------|
| `Empleado` | nombre, apellido, cédula (validación EC), cargo (vendedor/bodega/admin), salario, fecha ingreso, activo |

### `tareas` — Tareas (creado para estudio de FK)

| Modelo | Descripción | FK |
|--------|-------------|----|
| `Tarea` | titulo, descripcion, prioridad, completada, fecha vencimiento | FK → `empleados.Empleado` |

### `transaccion.security` — Seguridad (sub-app)

Gestiona usuarios, grupos (roles) y permisos usando autenticación nativa de
Django. No tiene modelos propios.

---

## URLs del sistema

| Ruta | App | Namespace |
|------|-----|-----------|
| `/` | Billing (home, listados CRUD) | `billing` |
| `/admin/` | Django Admin | `admin` |
| `/accounts/` | Autenticación (login/logout) | `auth` |
| `/empleados/` | Empleados | `empleados` |
| `/tareas/` | Tareas | `tareas` |
| `/purchases/` | Compras | `purchasing` |
| `/transacciones/` | Transacciones | `transaccion` |
| `/security/` | Usuarios, roles, permisos | `security` |

---

## Patrón CRUD (CBV) — usado en empleados y tareas

Ejemplo del patrón con vistas genéricas de Django:

```python
# urls.py
app_name = 'ejemplo'
urlpatterns = [
    path('',           EjemploListView.as_view(),   name='list'),
    path('nuevo/',     EjemploCreateView.as_view(), name='create'),
    path('<int:pk>/editar/',  EjemploUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', EjemploDeleteView.as_view(), name='delete'),
]
```

Cada vista hereda de `ListView`, `CreateView`, `UpdateView` o `DeleteView`.
El formulario usa `ModelForm` con widgets personalizados.

---

## Características del sistema

### CRUD genérico con mixins (Brand, ProductGroup, Supplier, Customer, Product)

Reutiliza 5 mixins (`shared/mixins.py`):

- **`DynamicColumnsMixin`** — selección de columnas visibles, persistida en sesión.
- **`GenericFilterMixin`** — filtros declarativos de texto y booleanos.
- **`ExportListMixin`** — exportación a PDF y Excel del listado filtrado.
- **`ListFeaturesMixin`** — combinación de los tres anteriores.
- **`GenericDetailMixin`** — vista de detalle con campos declarativos.

Tres plantillas genéricas (`_generic_list.html`, `_generic_form.html`,
`_generic_detail.html`) renderizan cualquier modelo.

### Exportación a PDF y Excel

Botones en listados. Soporta:
- Columnas dinámicas (elige qué exportar).
- Orientación automática (vertical/horizontal) según número de columnas.
- Ancho de columnas autoajustado.

### Validación de cédula ecuatoriana

`shared/validators.py` — implementa el algoritmo Módulo 10 del Registro Civil
para validar cédulas (10 dígitos) y RUC (13 dígitos).

### Cálculos financieros

`shared/money.py` — IVA 15%, redondeo a 2 decimales.

### Auditoría

`shared/decorators.py` — `@audit_action('ACCION')` registra en consola cada
operación importante.

### Seguridad

- Login obligatorio (`LoginRequiredMixin`).
- Eliminación restringida a personal **staff** (`StaffRequiredMixin`).
- Roles personalizados (`GroupRequiredMixin`): Administrador, Vendedor, Analista de Compras.
- Comando `setup_roles` para crear los grupos con sus permisos.

---

## Dependencias principales

| Paquete | Versión | Uso |
|---------|---------|-----|
| Django | 6.0.6 | Framework |
| pillow | 12.2 | Imágenes |
| openpyxl | 3.1 | Exportar Excel |
| reportlab | 5.0 | Exportar PDF |
| django-extensions | 4.1 | Utilidades de desarrollo |
| ipython | 9.14 | Shell interactiva |

---

## Notas técnicas

- El campo `Customer.dni` valida cédula/RUC ecuatoriano.
- Borrar (Delete) en grupos, proveedores, productos y clientes requiere usuario **staff**.
- Las vistas de Brand registran auditoría en consola (`@audit_action`).
- Las transacciones se auto-generan al crear facturas y compras.
- Stock se actualiza automáticamente al crear/editar/eliminar compras y
  transacciones.
- Los CRUDs de empleados y tareas usan el patrón CBV simple (sin mixins),
  ideal para estudiar el funcionamiento de Django por capas.
