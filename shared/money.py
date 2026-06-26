"""Cálculos monetarios centralizados (IVA y totales).

Tener una sola fuente para el IVA y el redondeo evita inconsistencias entre
facturas y compras, y garantiza que `total == subtotal + tax` con exactamente
2 decimales, sin depender del redondeo del backend de base de datos.
"""
from decimal import Decimal, ROUND_HALF_UP

TAX_RATE = Decimal('0.15')   # IVA 15%
CENTS = Decimal('0.01')


def money(value):
    """Redondea a 2 decimales (centavos) con redondeo bancario estándar."""
    return Decimal(value).quantize(CENTS, rounding=ROUND_HALF_UP)


def compute_totals(subtotal, rate=TAX_RATE):
    """Devuelve (subtotal, tax, total) ya redondeados a 2 decimales.

    total se calcula como subtotal + tax (ambos redondeados) para que la suma
    mostrada siempre cuadre.
    """
    subtotal = money(subtotal)
    tax = money(subtotal * rate)
    total = subtotal + tax
    return subtotal, tax, total
