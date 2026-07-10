from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('purchases/', include('purchasing.urls')),  
    path('', include('billing.urls')),
    path('transacciones/', include('transaccion.urls')),
    path('security/', include('transaccion.security.urls')),
    path('empleados/', include('empleados.urls')),
    path('tareas/', include('tareas.urls')),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
