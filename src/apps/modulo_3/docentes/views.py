from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin

from .models import Docente
from .forms import DocenteForm

class DocenteListView(ListView):
    """
    Vista para listar todos los Docentes (CRUD - Read)
    """
    model = Docente
    template_name = 'docentes/docente_list.html'
    context_object_name = 'docentes'

class DocenteCreateView(SuccessMessageMixin, CreateView):
    """
    Vista para crear un nuevo Docente (CRUD - Create)
    """
    model = Docente
    form_class = DocenteForm
    template_name = 'docentes/docente_form.html'
    success_url = reverse_lazy('docentes:docente_list')
    success_message = "Docente creado correctamente."
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Nuevo Docente'
        return context

class DocenteUpdateView(SuccessMessageMixin, UpdateView):
    """
    Vista para actualizar un Docente (CRUD - Update)
    """
    model = Docente
    form_class = DocenteForm
    template_name = 'docentes/docente_form.html'
    success_url = reverse_lazy('docentes:docente_list')
    success_message = "Docente actualizado correctamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Docente'
        return context

class DocenteDeleteView(SuccessMessageMixin, DeleteView):
    """
    Vista para eliminar un Docente (CRUD - Delete)
    Al borrar el Docente, se borra el Usuario y la Persona (por on_delete=CASCADE)
    """
    model = Docente
    template_name = 'docentes/docente_confirm_delete.html'
    success_url = reverse_lazy('docentes:docente_list')
    success_message = "Docente eliminado correctamente."
