from django.urls import path
from .views import TareaListView, TareaCreateView, TareaUpdateView, TareaDeleteView

app_name = 'tareas'

urlpatterns = [
    path('', TareaListView.as_view(), name='list'),
    path('nueva/', TareaCreateView.as_view(), name='create'),
    path('<int:pk>/editar/', TareaUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', TareaDeleteView.as_view(), name='delete'),
]
