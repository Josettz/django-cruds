from django import forms
from .models import Tarea


class TareaForm(forms.ModelForm):
    class Meta:
        model = Tarea
        fields = ['empleado', 'titulo', 'descripcion', 'prioridad', 'fecha_vencimiento', 'completada']
        widgets = {
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }
