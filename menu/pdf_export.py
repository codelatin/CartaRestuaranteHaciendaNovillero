"""Genera una carta PDF nueva con los datos actuales de Django.

Compatible con los modelos del proyecto Hacienda El Novillero:
Categoria, ConfiguracionSitio, Item, Variante, BloqueMenu y BloqueMenuItem.
"""
from io import BytesIO
from PIL import Image as PILImage
from PIL import ImageDraw as PILImageDraw
from PIL import ImageOps
from xml.sax.saxutils import escape

from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.contrib.staticfiles import finders
from django.http import HttpResponse

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image as PDFImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import BloqueMenu, BloqueMenuItem, Categoria, ConfiguracionSitio, Item


CREMA = colors.HexColor("#F4ECE0")
VERDE = colors.HexColor("#3F4A3C")
DORADO = colors.HexColor("#B89B5E")
ACENTO = colors.HexColor("#B5541F")
TINTA = colors.HexColor("#36382F")


def _p(texto, estilo):
    """Construye un Paragraph seguro, conservando saltos de línea."""
    texto = escape(str(texto or "")).replace("\r\n", "\n").replace("\n", "<br/>")
    return Paragraph(texto, estilo)


def _imagen_ajustada(campo_imagen, max_ancho, max_alto):
    """Devuelve una imagen proporcional; si no está disponible, devuelve None."""
    if not campo_imagen:
        return None
    try:
        origen = campo_imagen.path
    except (ValueError, NotImplementedError, OSError):
        try:
            origen = BytesIO(campo_imagen.read())
        except Exception:
            return None
    try:
        imagen = PDFImage(origen)
        factor = min(max_ancho / float(imagen.imageWidth), max_alto / float(imagen.imageHeight))
        imagen.drawWidth = imagen.imageWidth * factor
        imagen.drawHeight = imagen.imageHeight * factor
        imagen.hAlign = "CENTER"
        return imagen
    except Exception:
        return None

def _imagen_circular(campo_imagen, diametro):
    """Recorta una fotografía en círculo para usarla en el PDF."""
    if not campo_imagen:
        return None

    salida = None

    try:
        # Obtiene la imagen desde el almacenamiento de Django.
        try:
            origen = campo_imagen.path
        except (ValueError, NotImplementedError, OSError, AttributeError):
            campo_imagen.open("rb")
            try:
                origen = BytesIO(campo_imagen.read())
            finally:
                campo_imagen.close()

        # Abre y corrige la orientación de la fotografía.
        with PILImage.open(origen) as original:
            imagen = ImageOps.exif_transpose(original).convert("RGBA")

            # Recorta un cuadrado centrado para evitar deformaciones.
            ancho, alto = imagen.size
            lado = min(ancho, alto)

            izquierda = (ancho - lado) // 2
            arriba = (alto - lado) // 2

            imagen = imagen.crop((
                izquierda,
                arriba,
                izquierda + lado,
                arriba + lado,
            ))

            # Redimensiona conservando una buena calidad.
            remuestreo = getattr(
                getattr(PILImage, "Resampling", PILImage),
                "LANCZOS",
            )
            imagen = imagen.resize((600, 600), remuestreo)

            # Crea una máscara circular transparente.
            mascara = PILImage.new("L", (600, 600), 0)
            dibujo = PILImageDraw.Draw(mascara)
            dibujo.ellipse((0, 0, 599, 599), fill=255)

            imagen.putalpha(mascara)

            # Guarda el PNG circular en memoria.
            salida = BytesIO()
            imagen.save(salida, format="PNG")
            salida.seek(0)

        foto = PDFImage(
            salida,
            width=diametro,
            height=diametro,
            mask="auto",
        )
        foto.hAlign = "CENTER"

        # Mantiene el archivo en memoria mientras se genera el PDF.
        foto._buffer_circular = salida

        return foto

    except Exception:
        if salida is not None:
            salida.close()
        return None


def _estilos():
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle(
            "CartaTitulo", parent=base["Title"], fontName="Helvetica", fontSize=22,
            leading=27, alignment=TA_CENTER, textColor=VERDE, spaceAfter=7,
        ),
        "subtitulo": ParagraphStyle(
            "CartaSubtitulo", parent=base["Normal"], fontName="Helvetica", fontSize=9,
            leading=13, alignment=TA_CENTER, textColor=TINTA, spaceAfter=8,
        ),
        "categoria": ParagraphStyle(
            "CartaCategoria", parent=base["Heading1"], fontName="Helvetica", fontSize=17,
            leading=21, alignment=TA_CENTER, textColor=VERDE, spaceBefore=13, spaceAfter=8,
        ),
        "nombre": ParagraphStyle(
            "CartaNombre", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=8.8,
            leading=11, textColor=VERDE, spaceAfter=2,
        ),
        "precio": ParagraphStyle(
            "CartaPrecio", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=8.8,
            leading=11, textColor=VERDE, alignment=TA_RIGHT,
        ),
        "descripcion": ParagraphStyle(
            "CartaDescripcion", parent=base["Normal"], fontName="Helvetica", fontSize=8,
            leading=10, textColor=TINTA, spaceAfter=1,
        ),
        "variante": ParagraphStyle(
            "CartaVariante", parent=base["Normal"], fontName="Helvetica", fontSize=8,
            leading=10, textColor=TINTA,
        ),
        "nota": ParagraphStyle(
            "CartaNota", parent=base["Normal"], fontName="Helvetica-BoldOblique", fontSize=9,
            leading=12, alignment=TA_CENTER, textColor=VERDE,
        ),
        "pie": ParagraphStyle(
            "CartaPie", parent=base["Normal"], fontName="Helvetica-Oblique", fontSize=7.2,
            leading=9, textColor=TINTA, spaceAfter=4,
        ),
        "contacto": ParagraphStyle(
            "CartaContacto", parent=base["Normal"], fontName="Helvetica", fontSize=8,
            leading=11, textColor=VERDE, alignment=TA_CENTER,
        ),
    }


def _tabla_platos(platos, ancho, estilos):
    """Crea una lista de nombres, descripciones y precios dentro de una columna."""
    ancho_precio = min(1.05 * inch, ancho * 0.28)
    ancho_nombre = ancho - ancho_precio
    filas = []
    spans_descripciones = []
    filas_variantes = []

    for plato in platos:
        precio = plato.precio_fmt if plato.precio is not None and not plato.variantes.all() else ""
        filas.append([
            Paragraph(escape(plato.nombre.upper()), estilos["nombre"]),
            Paragraph(escape(precio), estilos["precio"]),
        ])
        if plato.descripcion:
            indice = len(filas)
            filas.append([_p(plato.descripcion, estilos["descripcion"]), ""])
            spans_descripciones.append(indice)

        variantes = list(plato.variantes.all())
        for variante in variantes:
            filas.append([
                Paragraph(escape(variante.nombre), estilos["variante"]),
                Paragraph(escape(variante.precio_fmt), estilos["precio"]),
            ])
            filas_variantes.append(len(filas) - 1)
        filas.append([Spacer(1, 2), ""])

    if not filas:
        return Paragraph("", estilos["descripcion"])

    tabla = Table(filas, colWidths=[ancho_nombre, ancho_precio], hAlign="LEFT")
    comandos = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]
    for fila in spans_descripciones:
        comandos.append(("SPAN", (0, fila), (1, fila)))
    tabla.setStyle(TableStyle(comandos))
    return tabla




def _obtener_bloques(categoria):
    """Obtiene bloques activos con los platos disponibles y en su orden definido."""
    bloques = BloqueMenu.objects.filter(categoria=categoria, activo=True).order_by("orden", "id")
    resultado = []
    usados = set()
    for bloque in bloques:
        asignaciones = (
            BloqueMenuItem.objects.filter(bloque=bloque, item__disponible=True)
            .select_related("item")
            .prefetch_related("item__variantes")
            .order_by("orden", "id")
        )
        platos = []
        for asignacion in asignaciones:
            if asignacion.item.categoria_id != categoria.pk:
                continue
            if asignacion.item_id in usados:
                continue
            platos.append(asignacion.item)
            usados.add(asignacion.item_id)
        if platos:
            resultado.append((bloque, platos))
    return resultado, usados


def _pagina_fondo(canvas, doc):
    """Fondo crema y pie discreto en cada página."""
    canvas.saveState()
    ancho, alto = doc.pagesize
    canvas.setFillColor(CREMA)
    canvas.rect(0, 0, ancho, alto, stroke=0, fill=1)
    canvas.setStrokeColor(DORADO)
    canvas.setLineWidth(0.7)
    canvas.line(doc.leftMargin, 0.43 * inch, ancho - doc.rightMargin, 0.43 * inch)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(VERDE)
    canvas.drawRightString(ancho - doc.rightMargin, 0.25 * inch, f"Hacienda El Novillero  ·  Página {doc.page}")
    canvas.restoreState()


@staff_member_required(login_url="admin:login")
def descargar_carta_pdf(request):
    """Genera y descarga una carta PDF nueva a partir de los datos guardados."""
    if not request.user.has_perm("menu.view_item"):
        raise PermissionDenied("No tienes permiso para descargar la carta.")

    config = ConfiguracionSitio.cargar()
    estilos = _estilos()

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.62 * inch,
        leftMargin=0.62 * inch,
        topMargin=0.48 * inch,
        bottomMargin=0.62 * inch,
        title=f"Menú - {config.nombre}",
        author=config.nombre,
    )
    historia = []

    ruta_logo = finders.find("menu/images/logo_hacienda.png")
    if ruta_logo:
        logo = _imagen_ajustada(type("ImagenStatic", (), {"path": ruta_logo})(), 1.65 * inch, 1.10 * inch)
        if logo:
            historia.extend([logo, Spacer(1, 5)])

    historia.append(Paragraph("M E N Ú", estilos["titulo"]))
    historia.append(Paragraph(escape(config.nombre), estilos["subtitulo"]))

    contactos = []
    if config.telefono:
        contactos.append(f"Reservas: {config.telefono}")
    if config.instagram:
        contactos.append(f"Instagram: @{config.instagram.lstrip('@')}")
    if config.facebook:
        contactos.append(f"Facebook: {config.facebook}")
    if config.email:
        contactos.append(config.email)
    if contactos:
        historia.append(Paragraph(escape("   ·   ".join(contactos)), estilos["contacto"]))
        historia.append(Spacer(1, 10))

    categorias = Categoria.objects.filter(activa=True).order_by("orden", "nombre")
    ancho_util = doc.width
    ancho_foto = 1.58 * inch
    ancho_texto = ancho_util - ancho_foto - 0.14 * inch
    hubo_platos = False

    for categoria in categorias:
        platos_disponibles = list(
            Item.objects.filter(categoria=categoria, disponible=True)
            .prefetch_related("variantes", "etiquetas")
            .order_by("orden", "nombre")
        )
        if not platos_disponibles:
            continue
        hubo_platos = True

        historia.append(Paragraph(escape(categoria.nombre), estilos["categoria"]))
        if categoria.nota:
            nota = Table([[Paragraph(escape(categoria.nota), estilos["nota"])]], colWidths=[ancho_util])
            nota.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            historia.extend([nota, Spacer(1, 8)])

        bloques, usados = _obtener_bloques(categoria)
        for bloque, platos_bloque in bloques:
            tabla_platos = _tabla_platos(platos_bloque, ancho_texto, estilos)
            diametro_foto = min(ancho_foto - 0.08 * inch,1.78 * inch,)
            foto = _imagen_circular(bloque.imagen,diametro_foto,)
            if foto:
                if bloque.lado_imagen == BloqueMenu.DERECHA:
                    fila = [tabla_platos, foto]
                    anchos = [ancho_texto, ancho_foto]
                else:
                    fila = [foto, tabla_platos]
                    anchos = [ancho_foto, ancho_texto]
                bloque_tabla = Table([fila], colWidths=anchos, hAlign="LEFT")
                bloque_tabla.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]))
                historia.append(bloque_tabla)
            else:
                historia.append(_tabla_platos(platos_bloque, ancho_util, estilos))
            historia.append(Spacer(1, 8))

        sueltos = [p for p in platos_disponibles if p.pk not in usados]
        if sueltos:
            historia.append(_tabla_platos(sueltos, ancho_util, estilos))
            historia.append(Spacer(1, 8))

    if not hubo_platos:
        historia.append(Paragraph("No hay platos disponibles para mostrar en este momento.", estilos["subtitulo"]))

    historia.append(Spacer(1, 16))
    if config.nota_precios:
        historia.append(Paragraph(f"<b>{escape(config.nota_precios)}</b>", estilos["pie"]))
    if config.nota_legal:
        historia.append(_p(config.nota_legal, estilos["pie"]))
    if config.nota_alergenos:
        historia.append(_p(config.nota_alergenos, estilos["pie"]))

    doc.build(historia, onFirstPage=_pagina_fondo, onLaterPages=_pagina_fondo)
    pdf = buffer.getvalue()
    buffer.close()

    respuesta = HttpResponse(pdf, content_type="application/pdf")
    respuesta["Content-Disposition"] = 'attachment; filename="carta_hacienda_el_novillero.pdf"'
    respuesta["Cache-Control"] = "no-store, max-age=0"
    return respuesta
