from django.db.models.signals import post_save
from django.dispatch import receiver
from purchasing.models import Purchase
from billing.models import Invoice
from .models import Transaccion


@receiver(post_save, sender=Purchase)
def crear_transaccion_por_compra(sender, instance, created, **kwargs):
    Transaccion.objects.update_or_create(
        compra=instance,
        defaults={
            'descripcion': f'Compra #{instance.id} - {instance.supplier}',
            'monto': instance.total,
            'iva': instance.tax,
            'tipo': 'egreso',
        }
    )


@receiver(post_save, sender=Invoice)
def crear_transaccion_por_factura(sender, instance, created, **kwargs):
    Transaccion.objects.update_or_create(
        factura=instance,
        defaults={
            'descripcion': f'Factura #{instance.id} - {instance.customer}',
            'monto': instance.total,
            'iva': instance.tax,
            'tipo': 'ingreso',
        }
    )