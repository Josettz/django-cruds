from django.db import models
from empleados.models import Empleado


class Tarea(models.Model):
    PRIORIDAD = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
    ]

    empleado = models.ForeignKey(
        Empleado, on_delete=models.CASCADE, related_name='tareas',
        verbose_name='Asignado a'
    )
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD, default='media')
    completada = models.BooleanField(default=False)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Tarea'
        verbose_name_plural = 'Tareas'

    def __str__(self):
        return self.titulo
