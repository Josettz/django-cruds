from django.urls import path
from . import views

app_name = 'empleados'

urlpatterns = [
    path('', views.EmpleadoListView.as_view(), name='list'),
    path('nuevo/', views.EmpleadoCreateView.as_view(), name='create'),
    path('<int:pk>/editar/', views.EmpleadoUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', views.EmpleadoDeleteView.as_view(), name='delete'),
]