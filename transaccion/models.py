from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from billing.models import Invoice, Product
from purchasing.models import Purchase


class Transaccion(models.Model):
    TIPO_CHOICES = [
        ('ingreso', 'Ingreso'),
        ('egreso', 'Egreso'),
    ]

    descripcion = models.CharField(max_length=200)
    monto = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    iva = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    fecha = models.DateTimeField(auto_now_add=True)

    # Conexión con el resto del sistema: solo UNA de las dos debe tener valor
    factura = models.ForeignKey(Invoice, on_delete=models.CASCADE, null=True, blank=True, related_name='transacciones')
    compra = models.ForeignKey(Purchase, on_delete=models.CASCADE, null=True, blank=True, related_name='transacciones')

    class Meta:
        ordering = ['-fecha']
        constraints = [
            models.CheckConstraint(condition=models.Q(monto__gt=0), name='monto_positivo'),
        ]

    @property
    def subtotal(self):
        return self.monto - self.iva

    @property
    def total(self):
        return self.monto

    def __str__(self):
        return f'{self.descripcion} - {self.monto}'


class TransaccionDetail(models.Model):
    transaccion = models.ForeignKey(Transaccion, on_delete=models.CASCADE, related_name='detalles')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='transaccion_details')
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)