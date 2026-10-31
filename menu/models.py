from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


def formatear_cop(valor):
    """16000 -> '$16.000' (formato del menú del cliente)."""
    return "$" + f"{valor:,}".replace(",", ".")


class ConfiguracionSitio(models.Model):
    """Datos generales editables. Solo existe un registro (singleton)."""

    nombre = models.CharField(max_length=120, default="Hacienda El Novillero")
    # ======================================================
    # TIPOGRAFÍA DEL MENÚ
    # ======================================================

    FUENTES_MENU = [
        ("Poppins", "Poppins - Moderna y elegante"),
        ("Montserrat", "Montserrat - Profesional"),
        ("Lato", "Lato - Clara y sencilla"),
        ("Playfair Display", "Playfair Display - Clásica"),
        ("Merriweather", "Merriweather - Tradicional"),
        ("Nunito", "Nunito - Suave y amigable"),
    ]

    
    # ==========================================
    # TAMAÑO DE LETRA DEL MENÚ
    # ==========================================

    TAMANOS_LETRA = [
        ("14", "Pequeño - 14 px"),
        ("16", "Normal - 16 px"),
        ("18", "Grande - 18 px"),
        ("20", "un poco mas grande - 20 px"),
        ("22", "aun mas grande - 22 px"),
        ("60", "Mega grande - 60 px"),

    ]

    tamano_letra = models.CharField(
        max_length=2,
        choices=TAMANOS_LETRA,
        default="16",
        verbose_name="Tamaño de letra del menú",
        help_text="Selecciona el tamaño de los textos del menú."
    )


    fuente_menu = models.CharField(
        max_length=50,
        choices=FUENTES_MENU,
        default="Poppins",
        verbose_name="Tipo de letra del menú",
        help_text="Selecciona la fuente que se utilizará en toda la carta.",
    )
    descripcion = models.TextField(
        blank=True,
        help_text="Texto de presentación de la hacienda.",
    )
    telefono = models.CharField(max_length=40, blank=True)
    instagram = models.CharField(max_length=80, blank=True, help_text="Sin @")
    facebook = models.CharField(max_length=80, blank=True)
    email = models.EmailField(blank=True)
    nota_precios = models.CharField(
        max_length=200,
        blank=True,
        default="Todos nuestros precios incluyen impuesto al consumo",
    )
    nota_legal = models.TextField(
        blank=True,
        help_text="Aviso de imágenes de referencia y disponibilidad.",
    )
    nota_alergenos = models.TextField(blank=True)

    class Meta:
        verbose_name = "Configuración Hacienda El Novillero"
        verbose_name_plural = "Configuración Hacienda El Novillero"

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def cargar(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Etiqueta(models.Model):
    """Ej.: Vegetariano, Infantil, Sin lactosa."""

    nombre = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)


class Categoria(models.Model):
    nombre = models.CharField(max_length=80)
    slug = models.SlugField(max_length=90, unique=True, blank=True)
    nota = models.CharField(
        max_length=200,
        blank=True,
        help_text='Ej.: "Elige el acompañamiento con el que quieres complementar tu plato."',
    )
    imagen = models.ImageField(
        upload_to="categorias/",
        blank=True,
        help_text="Foto circular opcional de la categoría.",
    )
    orden = models.PositiveSmallIntegerField(default=0)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["orden", "nombre"]
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)


class Item(models.Model):
    categoria = models.ForeignKey(
        Categoria, on_delete=models.CASCADE, related_name="items"
    )
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    precio = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="En pesos, sin puntos (16000). Déjalo vacío si el plato usa variantes.",
    )
    imagen = models.ImageField(upload_to="items/", blank=True)
    etiquetas = models.ManyToManyField(Etiqueta, blank=True, related_name="items")
    disponible = models.BooleanField(
        default=True, help_text="Desmarca para ocultar un plato agotado."
    )
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["categoria__orden", "orden", "nombre"]
        verbose_name = "Plato"
        verbose_name_plural = "Platos"

    def __str__(self):
        return self.nombre

    @property
    def precio_fmt(self):
        return formatear_cop(self.precio) if self.precio is not None else ""


class Variante(models.Model):
    """Para platos con varios tamaños/precios."""

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="variantes")
    nombre = models.CharField(max_length=80)
    precio = models.PositiveIntegerField()
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["orden", "precio"]
        verbose_name = "Variante"
        verbose_name_plural = "Variantes"

    def __str__(self):
        return f"{self.item.nombre} - {self.nombre}"

    @property
    def precio_fmt(self):
        return formatear_cop(self.precio)


class BloqueMenu(models.Model):
    """Composición editorial: una fotografía que acompaña varios platos."""

    IZQUIERDA = "izquierda"
    DERECHA = "derecha"
    LADOS_IMAGEN = [
        (IZQUIERDA, "Izquierda"),
        (DERECHA, "Derecha"),
    ]

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        related_name="bloques_menu",
    )
    titulo = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nombre interno opcional para identificar el bloque en el administrador.",
    )
    imagen = models.ImageField(upload_to="bloques_menu/")
    lado_imagen = models.CharField(
        max_length=10,
        choices=LADOS_IMAGEN,
        default=IZQUIERDA,
    )
    orden = models.PositiveSmallIntegerField(default=0)
    activo = models.BooleanField(default=True)
    items = models.ManyToManyField(
        Item,
        through="BloqueMenuItem",
        related_name="bloques_menu",
        blank=True,
    )

    class Meta:
        ordering = ["categoria__orden", "orden", "id"]
        verbose_name = "Bloque visual del menú"
        verbose_name_plural = "Grupos  del menú"

    def __str__(self):
        if self.titulo and self.titulo.strip():
            return f"{self.categoria.nombre} - {self.titulo}"

        return f"{self.categoria.nombre} - Grupo {self.pk or 'nuevo'}"


class BloqueMenuItem(models.Model):
    """Asigna un plato a un bloque y controla su orden dentro de ese bloque."""

    bloque = models.ForeignKey(
        BloqueMenu,
        on_delete=models.CASCADE,
        related_name="platos_bloque",
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="asignaciones_bloque",
    )
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["orden", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["bloque", "item"],
                name="unique_item_en_bloque_menu",
            )
        ]
        verbose_name = "Plato del bloque"
        verbose_name_plural = "Platos del bloque"

    def __str__(self):
        return f"{self.item.nombre} en {self.bloque}"

    def clean(self):
        super().clean()
        if self.bloque_id and self.item_id:
            if self.bloque.categoria_id != self.item.categoria_id:
                raise ValidationError(
                    {"item": "El plato debe pertenecer a la misma categoría del bloque."}
                )
