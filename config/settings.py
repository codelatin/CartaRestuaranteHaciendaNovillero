

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "cartanovilleros.pythonanywhere.com",
]


# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'menu',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = 'es-co'

TIME_ZONE = 'America/Bogota'

USE_I18N = True

USE_TZ = True



# ======================================================
# ARCHIVOS ESTÁTICOS - HACIENDA EL NOVILLERO
# ======================================================

# URL para CSS, JavaScript, logos e imágenes del sistema
STATIC_URL = "/static/"

# Carpeta donde collectstatic reúne los archivos
STATIC_ROOT = BASE_DIR / "staticfiles"


# ======================================================
# ARCHIVOS MULTIMEDIA - FOTOGRAFÍAS DEL MENÚ
# ======================================================

# URL de las imágenes subidas desde Django Admin
MEDIA_URL = "/media/"

# Carpeta donde se guardan las fotografías
MEDIA_ROOT = BASE_DIR / "media"


# Email
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}


JAZZMIN_SETTINGS = {

    "site_title": "Hacienda El Novillero",
    "site_header": "Hacienda El Novillero",
    "site_brand": "Hacienda El Novillero",

    # LOGOS
    "site_logo": "menu/images/logo_hacienda.png",
    "login_logo": "menu/images/logo_hacienda.png",
    "login_logo_dark": "menu/images/logo_hacienda.png",

    "site_logo_classes": "img-fluid",

    "custom_css": "menu/css/jazzmin_custom.css",

    "site_icon": "menu/images/logo_hacienda.png",

    "welcome_sign": "Bienvenido a Hacienda El Novillero",
    "copyright": "Hacienda El Novillero",

     # ======================================================
    # MENÚ SUPERIOR - DESCARGA DE LA CARTA
    # ======================================================
    "topmenu_links": [
        {
            "name": "Descargar carta PDF",
            "url": "descargar_carta_pdf",
            "permissions": ["menu.view_item"],
        },
    ],

    # BUSCADOR
    "search_model": [
        "menu.Item",
        "menu.Categoria",
        "menu.Etiqueta",
        "menu.Variante",
    ],

    # MENÚ LATERAL
    "show_sidebar": True,
    "navigation_expanded": True,

    "order_with_respect_to": [
        "menu",
        "menu.configuracionsitio",
        "menu.categoria",
        "menu.bloquemenu",
        "menu.item",
        "menu.variante",
        "menu.etiqueta",
        "auth",
        "auth.user",
        "auth.group",
    ],

    # ICONOS
    "icons": {
        "menu": "fas fa-utensils",
        "menu.configuracionsitio": "fas fa-cog",
        "menu.categoria": "fas fa-layer-group",
        "menu.bloquemenu": "fas fa-images",
        "menu.item": "fas fa-utensils",
        "menu.variante": "fas fa-tags",
        "menu.etiqueta": "fas fa-bookmark",

        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.group": "fas fa-users",
    },

    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    "changeform_format": "horizontal_tabs",

    "related_modal_active": True,

    "show_ui_builder": True,
    "show_theme_chooser": True,

    "language_chooser": False,

    "use_google_fonts_cdn": True,
}