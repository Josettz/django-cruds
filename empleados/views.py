from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy 
from .models import Empleado
from .forms import EmpleadoForm
from datetime import date


class EmpleadoListView(ListView):
    model = Empleado
    template_name = 'empleados/empleado_list.html'
    context_object_name = 'empleados'

class EmpleadoCreateView(CreateView):
    model = Empleado
    form_class = EmpleadoForm
    template_name = 'empleados/empleado_form.html'
    success_url = reverse_lazy('empleados:list')

class EmpleadoDeleteView(DeleteView):
    model = Empleado
    template_name = 'empleados/empleado_confirm_delete.html'
    success_url = reverse_lazy('empleados:list')

class EmpleadoUpdateView(UpdateView):
    model = Empleado
    form_class = EmpleadoForm
    template_name = 'empleados/empleado_form.html'
    success_url = reverse_lazy('empleados:list')