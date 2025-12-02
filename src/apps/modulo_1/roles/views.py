from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import *

# Create your views here.
#Rol
class RolListView(ListView):
    model = Rol
    template_name = 'roles/rol_list.html'

class RolCreateView(CreateView):
    model = Rol
    template_name = 'roles/rol_form.html'
    fields = '__all__'
    success_url = reverse_lazy('rol_list')

class RolUpdateView(UpdateView):
    model = Rol
    template_name = 'roles/rol_form.html'
    fields = '__all__'
    success_url = reverse_lazy('rol_list')

class RolDeleteView(DeleteView):
    model = Rol
    template_name = 'roles/rol_confirm_delete.html'
    success_url = reverse_lazy('rol_list')

#Docente
class DocenteListView(ListView):
    model = Docente
    template_name = 'roles/docente_list.html'

class DocenteCreateView(CreateView):
    model = Docente
    template_name = 'roles/docente_form.html'
    fields = '__all__'
    success_url = reverse_lazy('docente_list')

class DocenteUpdateView(UpdateView):
    model = Docente
    template_name = 'roles/docente_form.html'
    fields = '__all__'
    success_url = reverse_lazy('docente_list')

class DocenteDeleteView(DeleteView):
    model = Docente
    template_name = 'roles/docente_confirm_delete.html'
    success_url = reverse_lazy('docente_list')

#Estudiante
class EstudianteListView(ListView):
    model = Estudiante
    template_name = 'roles/estudiante_list.html'

class EstudianteCreateView(CreateView):
    model = Estudiante
    template_name = 'roles/estudiante_form.html'
    fields = '__all__'
    success_url = reverse_lazy('estudiante_list')

class EstudianteUpdateView(UpdateView):
    model = Estudiante
    template_name = 'roles/estudiante_form.html'
    fields = '__all__'
    success_url = reverse_lazy('estudiante_list')

class EstudianteDeleteView(DeleteView):
    model = Estudiante
    template_name = 'roles/estudiante_confirm_delete.html'
    success_url = reverse_lazy('estudiante_list')

#Tutor
class TutorListView(ListView):
    model = Tutor
    template_name = 'roles/tutor_list.html'

class TutorCreateView(CreateView):
    model = Tutor
    template_name = 'roles/tutor_form.html'
    fields = '__all__'
    success_url = reverse_lazy('tutor_list')

class TutorUpdateView(UpdateView):
    model = Tutor
    template_name = 'roles/tutor_form.html'
    fields = '__all__'
    success_url = reverse_lazy('tutor_list')

class TutorDeleteView(DeleteView):
    model = Tutor
    template_name = 'roles/tutor_confirm_delete.html'
    success_url = reverse_lazy('tutor_list')

#TutorEstudiante
class TutorEstudianteListView(ListView):
    model = TutorEstudiante
    template_name = 'roles/tutorestudiante_list.html'

class TutorEstudianteCreateView(CreateView):
    model = TutorEstudiante
    template_name = 'roles/tutorestudiante_form.html'
    fields = '__all__'
    success_url = reverse_lazy('tutorestudiante_list')

class TutorEstudianteUpdateView(UpdateView):
    model = TutorEstudiante
    template_name = 'roles/tutorestudiante_form.html'
    fields = '__all__'
    success_url = reverse_lazy('tutorestudiante_list')

class TutorEstudianteDeleteView(DeleteView):
    model = TutorEstudiante
    template_name = 'roles/tutorestudiante_confirm_delete.html'
    success_url = reverse_lazy('tutorestudiante_list')

#UsuarioRol (Posiblemente innecesario)
class UsuarioRolListView(ListView):
    model = UsuarioRol
    template_name = 'roles/usuariorol_list.html'

class UsuarioRolCreateView(CreateView):
    model = UsuarioRol
    template_name = 'roles/usuariorol_form.html'
    fields = '__all__'
    success_url = reverse_lazy('usuariorol_list')

class UsuarioRolUpdateView(UpdateView):
    model = UsuarioRol
    template_name = 'roles/usuariorol_form.html'
    fields = '__all__'
    success_url = reverse_lazy('usuariorol_list')

class UsuarioRolDeleteView(DeleteView):
    model = UsuarioRol
    template_name = 'roles/usuariorol_confirm_delete.html'
    success_url = reverse_lazy('usuariorol_list')