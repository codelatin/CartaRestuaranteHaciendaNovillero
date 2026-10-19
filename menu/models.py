from django.db import models
from django.utils.text import slugify


def formatear_cop(valor):
    """16000 -> '$16.000' (formato del menú del cliente)."""
    return "$" + f"{valor:,}".replace(",", ".")


class ConfiguracionSitio(models.Model):
    """Datos generales editables. Solo existe un registro (singleton)."""

    nombre = models.CharField(max_length=120, default="Hacienda El Novillero")
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
        verbose_name = "Configuración del sitio"
        verbose_name_plural = "Configuración del sitio"

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        self.pk = 1  # fuerza un único registro
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
        help_text="Foto circular opcional que acompaña la sección.",
    )
    orden = models.PositiveSmallIntegerField(default=0)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["orden", "nombre"]

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
        verbose_name = "Plato"
        verbose_name_plural = "Platos"
        ordering = ["categoria__orden", "orden", "nombre"]

    def __str__(self):
        return self.nombre

    @property
    def precio_fmt(self):
        return formatear_cop(self.precio) if self.precio is not None else ""


class Variante(models.Model):
    """Para platos con varios tamaños/precios (ej.: Pizzeta 30 cm / Pizza 45 cm)."""

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="variantes")
    nombre = models.CharField(max_length=80)
    precio = models.PositiveIntegerField()
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["orden", "precio"]

    def __str__(self):
        return f"{self.item.nombre} - {self.nombre}"

    @property
    def precio_fmt(self):
        return formatear_cop(self.precio)