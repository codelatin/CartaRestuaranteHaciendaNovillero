from django.contrib import admin
from django.utils.html import format_html

from .models import Categoria, ConfiguracionSitio, Etiqueta, Item, Variante, BloqueMenu, BloqueMenuItem


class VarianteInline(admin.TabularInline):
    model = Variante
    extra = 0


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "precio", "disponible", "orden")
    list_editable = ("precio", "disponible", "orden")  # edición rápida en la lista
    list_filter = ("categoria", "disponible", "etiquetas")
    search_fields = ("nombre", "descripcion")
    filter_horizontal = ("etiquetas",)
    inlines = [VarianteInline]
    actions = ["marcar_agotado", "marcar_disponible"]

    @admin.action(description="Marcar como agotado")
    def marcar_agotado(self, request, queryset):
        queryset.update(disponible=False)

    @admin.action(description="Marcar como disponible")
    def marcar_disponible(self, request, queryset):
        queryset.update(disponible=True)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "orden", "activa")
    list_editable = ("orden", "activa")
    prepopulated_fields = {"slug": ("nombre",)}


@admin.register(Etiqueta)
class EtiquetaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug")


@admin.register(ConfiguracionSitio)
class ConfiguracionSitioAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not ConfiguracionSitio.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

# ==========================================================
# BLOQUES VISUALES DEL MENÚ
# ==========================================================

class BloqueMenuItemInline(admin.TabularInline):
    model = BloqueMenuItem
    extra = 1

    fields = ("item", "orden")
    ordering = ("orden", "id")

    verbose_name = "Plato en este bloque"
    verbose_name_plural = "Orden de los platos en este bloque"


@admin.register(BloqueMenu)
class BloqueMenuAdmin(admin.ModelAdmin):

    list_display = (
        "nombre_grupo",
        "categoria",
        "miniatura",
        "lado_imagen",
        "orden",
        "activo",
    )

    list_display_links = ("nombre_grupo",)

    list_filter = (
        "categoria",
        "lado_imagen",
        "activo",
    )

    search_fields = (
        "titulo",
        "categoria__nombre",
    )

    list_editable = (
        "lado_imagen",
        "orden",
        "activo",
    )

    ordering = (
        "categoria__orden",
        "orden",
        "id",
    )

    inlines = (BloqueMenuItemInline,)

    exclude = ("items",)

    fieldsets = (
        (
            "Composición visual",
            {
                "fields": (
                    "categoria",
                    "titulo",
                    "imagen",
                    "lado_imagen",
                    "orden",
                    "activo",
                )
            },
        ),
    )

    # Nombre automático para grupos sin título
    @admin.display(description="Nombre del grupo", ordering="titulo")
    def nombre_grupo(self, obj):
        if obj.titulo and obj.titulo.strip():
            return obj.titulo

        return f"Grupo {obj.pk} - Sin título"

    # IMPORTANTE:
    # Conserva aquí el método miniatura que
    # ya tienes definido en tu admin.py.


    @admin.display(description="Fotografía")
    def miniatura(self, obj):
        if not obj.imagen:
            return "Sin imagen"

        return format_html(
            '<img src="{}" '
            'style="width:64px;height:64px;'  
            'object-fit:cover;border-radius:50%;" alt="">',
            obj.imagen.url,
        )

