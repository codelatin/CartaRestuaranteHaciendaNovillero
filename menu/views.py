import unicodedata

from django.db.models import Prefetch
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

from .models import Categoria, ConfiguracionSitio, Etiqueta, Item


def normalizar(texto):
    """Minúsculas y sin tildes: 'Champiñón' -> 'champinon'."""
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def agrupar_items(q="", etiqueta=""):
    """Devuelve [(categoria, [items])] aplicando búsqueda y etiqueta.

    El filtro de texto se hace en Python para ignorar tildes en cualquier base
    de datos (SQLite no lo hace con icontains). Con ~100 ítems es instantáneo.
    """
    items_qs = (
        Item.objects.filter(disponible=True)
        .prefetch_related("variantes", "etiquetas")
        .order_by("orden", "nombre")
    )
    if etiqueta:
        items_qs = items_qs.filter(etiquetas__slug=etiqueta)

    categorias = Categoria.objects.filter(activa=True).prefetch_related(
        Prefetch("items", queryset=items_qs, to_attr="items_visibles")
    )

    q_norm = normalizar(q.strip())
    grupos = []
    for cat in categorias:
        items = cat.items_visibles
        if q_norm:
            items = [
                i
                for i in items
                if q_norm in normalizar(f"{i.nombre} {i.descripcion} {cat.nombre}")
            ]
        if items:
            grupos.append((cat, items))
    return grupos


def _contexto_busqueda(request):
    q = request.GET.get("q", "")
    etiqueta = request.GET.get("etiqueta", "")
    return {
        "grupos": agrupar_items(q, etiqueta),
        "q": q,
        "etiqueta_activa": etiqueta,
    }


@require_GET
def menu(request):
    """Página completa."""
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
        # Si alguien abre /buscar/ directo en el navegador, lo mandamos al menú.
        query = request.META.get("QUERY_STRING", "")
        return redirect(f"/?{query}" if query else "/")
    return render(request, "menu/_resultados.html", _contexto_busqueda(request))