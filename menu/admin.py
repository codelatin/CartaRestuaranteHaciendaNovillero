from django.contrib import admin

from .models import Categoria, ConfiguracionSitio, Etiqueta, Item, Variante


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