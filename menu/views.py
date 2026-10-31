import unicodedata

from django.db.models import Prefetch
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

from .models import (
    BloqueMenu,
    BloqueMenuItem,
    Categoria,
    ConfiguracionSitio,
    Etiqueta,
    Item,
)


def normalizar(texto):
    """Minúsculas y sin tildes: 'Champiñón' -> 'champinon'."""
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def _items_visibles(etiqueta=""):
    qs = (
        Item.objects.filter(disponible=True)
        .prefetch_related("variantes", "etiquetas")
        .order_by("orden", "nombre")
    )
    if etiqueta:
        qs = qs.filter(etiquetas__slug=etiqueta).distinct()
    return qs


def _contexto_busqueda(request):
    """Devuelve bloques editoriales en vista normal y una lista en búsqueda.

    Los platos que todavía no se han asignado a un bloque siguen apareciendo,
    para que agregar esta función no oculte los datos actuales del restaurante.
    """
    q = request.GET.get("q", "").strip()
    etiqueta = request.GET.get("etiqueta", "")
    hay_filtros = bool(q or etiqueta)
    items_qs = _items_visibles(etiqueta)

    if hay_filtros:
        categorias = Categoria.objects.filter(activa=True).prefetch_related(
            Prefetch("items", queryset=items_qs, to_attr="items_visibles")
        )
        q_norm = normalizar(q)
        grupos = []

        for categoria in categorias:
            items = categoria.items_visibles
            if q_norm:
                items = [
                    item
                    for item in items
                    if q_norm
                    in normalizar(
                        f"{item.nombre} {item.descripcion} {categoria.nombre}"
                    )
                ]
            if items:
                grupos.append(
                    {
                        "categoria": categoria,
                        "bloques": [],
                        "items_sueltos": items,
                        "modo_busqueda": True,
                    }
                )

        return {
            "grupos": grupos,
            "q": q,
            "etiqueta_activa": etiqueta,
            "hay_filtros": True,
        }

    bloques_qs = (
        BloqueMenu.objects.filter(activo=True)
        .order_by("orden", "id")
        .prefetch_related(
            Prefetch(
                "platos_bloque",
                queryset=(
                    BloqueMenuItem.objects.filter(item__disponible=True)
                    .select_related("item")
                    .prefetch_related("item__variantes", "item__etiquetas")
                    .order_by("orden", "id")
                ),
                to_attr="asignaciones_visibles",
            )
        )
    )

    categorias = Categoria.objects.filter(activa=True).prefetch_related(
        Prefetch("items", queryset=items_qs, to_attr="items_visibles"),
        Prefetch("bloques_menu", queryset=bloques_qs, to_attr="bloques_visibles"),
    )

    grupos = []
    for categoria in categorias:
        bloques = []
        items_en_bloques = set()

        for bloque in categoria.bloques_visibles:
            asignaciones = getattr(bloque, "asignaciones_visibles", [])
            # Evita mostrar un bloque vacío si todavía no se le han asignado platos.
            asignaciones = [
                asignacion
                for asignacion in asignaciones
                if asignacion.item.categoria_id == categoria.id
            ]
            if asignaciones:
                bloque.asignaciones_visibles = asignaciones
                bloques.append(bloque)
                items_en_bloques.update(asignacion.item_id for asignacion in asignaciones)

        items_sueltos = [
            item for item in categoria.items_visibles if item.pk not in items_en_bloques
        ]

        if bloques or items_sueltos:
            grupos.append(
                {
                    "categoria": categoria,
                    "bloques": bloques,
                    "items_sueltos": items_sueltos,
                    "modo_busqueda": False,
                }
            )

    return {
        "grupos": grupos,
        "q": q,
        "etiqueta_activa": etiqueta,
        "hay_filtros": False,
    }


@require_GET
def menu(request):
    """Página completa del menú."""
    contexto = _contexto_busqueda(request)
    contexto.update(
        {
            "config": ConfiguracionSitio.cargar(),
            "etiquetas": Etiqueta.objects.all(),
        }
    )
    return render(request, "menu/menu.html", contexto)


@require_GET
def buscar(request):
    """Fragmento HTML que HTMX inserta en #resultados."""
    if not request.headers.get("HX-Request"):
        query = request.META.get("QUERY_STRING", "")
        return redirect(f"/?{query}" if query else "/")
    return render(request, "menu/_resultados.html", _contexto_busqueda(request))
