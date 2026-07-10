from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Tarea
from .forms import TareaForm


class TareaListView(ListView):
    model = Tarea
    template_name = 'tareas/tarea_list.html'
    context_object_name = 'tareas'


class TareaCreateView(CreateView):
    model = Tarea
    form_class = TareaForm
    template_name = 'tareas/tarea_form.html'
    success_url = reverse_lazy('tareas:list')


class TareaUpdateView(UpdateView):
    model = Tarea
    form_class = TareaForm
    template_name = 'tareas/tarea_form.html'
    success_url = reverse_lazy('tareas:list')


class TareaDeleteView(DeleteView):
    model = Tarea
    template_name = 'tareas/tarea_confirm_delete.html'
    success_url = reverse_lazy('tareas:list')
