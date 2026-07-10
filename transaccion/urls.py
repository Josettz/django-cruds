from django.urls import path
from .views import (
    TransaccionListView, TransaccionDetailView,
    TransaccionDeleteView,
    transaccion_create, transaccion_update,
)

urlpatterns = [
    path('', TransaccionListView.as_view(), name='transaccion_list'),
    path('crear/', transaccion_create, name='transaccion_create'),
    path('detalle/<int:pk>/', TransaccionDetailView.as_view(), name='transaccion_detail'),
    path('editar/<int:pk>/', transaccion_update, name='transaccion_update'),
    path('eliminar/<int:pk>/', TransaccionDeleteView.as_view(), name='transaccion_delete'),
]