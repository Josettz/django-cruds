from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date
from shared.validators import validate_cedula_ec


class Empleado(models.Model):
    CARGOS = [('vendedor', 'vendedor'),
               ('bodega', 'bodega'),
               ('admin', 'admin')
            ]     
    
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    cedula = models.CharField(max_length=10, unique=True, validators=[validate_cedula_ec])
    cargo = models.CharField(max_length=10, choices=CARGOS, default='vendedor')
    salario = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.1), MaxValueValidator(4000)])
    fecha_ingreso = models.DateField(default=date.today)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f'{self.apellido}, {self.nombre}'