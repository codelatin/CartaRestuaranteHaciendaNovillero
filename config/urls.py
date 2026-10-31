from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from menu.pdf_export import descargar_carta_pdf


urlpatterns = [
  
    path("admin/descargar-carta-pdf/",
        descargar_carta_pdf,
        name="descargar_carta_pdf",
    ),

    # Administrador de Django
    path("admin/", admin.site.urls),

    # Menú público del restaurante
    path("", include("menu.urls")),
]

# Archivos multimedia durante el desarrollo
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )