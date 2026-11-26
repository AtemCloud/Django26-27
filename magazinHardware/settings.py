"""
Setari pentru proiectul magazinHardware.

Valorile sensibile (parola bazei de date, parola de e-mail, SECRET_KEY) se citesc
din fisierul .env (vezi .env.example), astfel incat acelasi cod merge pe PC-ul de
acasa, pe PC-ul de la facultate si cu o baza de date in cloud.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(nume, implicit=None):
    return os.environ.get(nume, implicit)


def env_bool(nume, implicit=False):
    return str(env(nume, implicit)).lower() in ("1", "true", "yes", "da")


SECRET_KEY = env("SECRET_KEY", "django-insecure-schimba-ma-in-fisierul-env")
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = [h.strip() for h in env("ALLOWED_HOSTS", "localhost,127.0.0.1,.app.github.dev").split(",") if h.strip()]
# GitHub Codespaces: site-ul e servit prin https://<nume>-8000.app.github.dev
CSRF_TRUSTED_ORIGINS = ["https://*.app.github.dev"]
USE_X_FORWARDED_HOST = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "magazin.apps.MagazinConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Lab 1/2: IP-ul utilizatorului si obiectul Accesare pentru fiecare cerere
    "magazin.middleware.AccesareMiddleware",
]

ROOT_URLCONF = "magazinHardware.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Lab 2: datele firmei in footer
                "magazin.context_processors.date_firma",
                # Lab 4: categoriile din meniu
                "magazin.context_processors.categorii_meniu",
            ],
        },
    },
]

WSGI_APPLICATION = "magazinHardware.wsgi.application"

# ---------------------------------------------------------------- baza de date
# PostgreSQL e obligatoriu (Lab 4 cere ArrayField). Datele vin din .env.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", "magazin_hw"),
        "USER": env("DB_USER", "magazin"),
        "PASSWORD": env("DB_PASSWORD", ""),
        "HOST": env("DB_HOST", "localhost"),
        "PORT": env("DB_PORT", "5432"),
        "OPTIONS": {},
    }
}
# Varianta Neon CLI: "neon deploy" / "neon env pull" scrie in .env un DATABASE_URL (si DATABASE_URL_UNPOOLED).
# Daca DB_HOST nu e setat, folosim URL-ul direct (unpooled, necesar pentru search_path).
_url_neon = env("DATABASE_URL_UNPOOLED") or env("DATABASE_URL")
if _url_neon and not env("DB_HOST"):
    from urllib.parse import parse_qs, unquote, urlparse

    _u = urlparse(_url_neon)
    DATABASES["default"].update({
        "NAME": _u.path.lstrip("/"),
        "USER": unquote(_u.username or ""),
        "PASSWORD": unquote(_u.password or ""),
        "HOST": _u.hostname,
        "PORT": str(_u.port or 5432),
    })
    DATABASES["default"]["OPTIONS"]["sslmode"] = parse_qs(_u.query).get("sslmode", ["require"])[0]
    # Lab 3: utilizatorul propriu (din creare_user.sql) are prioritate fata de neondb_owner din URL
    if env("DB_USER"):
        DATABASES["default"]["USER"] = env("DB_USER")
        DATABASES["default"]["PASSWORD"] = env("DB_PASSWORD", "")

if env("DB_SCHEMA"):
    DATABASES["default"]["OPTIONS"]["options"] = f"-c search_path={env('DB_SCHEMA')},public"
if env("DB_SSLMODE"):
    DATABASES["default"]["OPTIONS"]["sslmode"] = env("DB_SSLMODE")

# Lab 6: utilizator personalizat (setat inainte de prima migrare, ca sa nu fie nevoie de reset mai tarziu)
AUTH_USER_MODEL = "magazin.Utilizator"
LOGIN_URL = "login"  # unde sunt trimisi utilizatorii nelogati (decoratorul @login_required)

# Curs 6: validatorii impliciti de parola sunt dezactivati doar cat timp proiectul e in dezvoltare (DEBUG)
if DEBUG:
    AUTH_PASSWORD_VALIDATORS = []
else:
    AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
        },
    ]

LANGUAGE_CODE = "ro"
TIME_ZONE = "Europe/Bucharest"
USE_I18N = True
# traducerile in romana care lipsesc din Django (admin, calendar, lista dubla de selectie): locale/ro/LC_MESSAGES
LOCALE_PATHS = [BASE_DIR / "locale"]
USE_TZ = True

STATIC_URL = "static/"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------- mesaje (Lab 5 Task 1, Curs 5)
from django.contrib.messages import constants as message_constants  # noqa: E402

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"
# MESSAGE_LEVEL = DEBUG ca sa apara si mesajele de tip debug (implicit Django le ascunde)
MESSAGE_LEVEL = message_constants.DEBUG if DEBUG else message_constants.INFO
# tagurile devin clase CSS in baza.html (mesaj-debug, mesaj-info ...), fiecare cu stilul ei in stil.css
MESSAGE_TAGS = {
    message_constants.DEBUG: "debug",
    message_constants.INFO: "info",
    message_constants.SUCCESS: "success",
    message_constants.WARNING: "warning",
    message_constants.ERROR: "error",
}

# ---------------------------------------------------------------- sesiuni (Lab 6)
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 24 * 60 * 60  # Lab 6: o zi, in secunde (vezi views.custom_login_view)

# ---------------------------------------------------------------- e-mail
# (nefolosit pana la Lab 7; mailurile ar aparea in consola)
MAILERS = {
    "default": {"BACKEND": "django.core.mail.backends.console.EmailBackend"},
}

# ---------------------------------------------------------------- date firma (Lab 2)
# Lab 2: datele firmei, trimise in toate paginile prin context processor (magazin/context_processors.py)
# si afisate in footer. Ultimele doua chei (program, cui) sunt cele "alese de noi".
DATE_FIRMA = {
    "nume": "Magazin Hardware SRL",
    "an_infiintare": 2015,
    "telefon": "0721 000 000",
    "adresa": "Str. Academiei 14, Bucuresti",
    "program": "Luni-Vineri 09:00-20:00, Sambata 10:00-16:00",
    "cui": "RO12345678",
}

# ---------------------------------------------------------------- constante proiect
K_PRODUSE_SIMILARE = 4  # Lab 4: cate produse din aceeasi categorie apar pe pagina produsului
STOC_MIN = 5  # Lab 4: sub aceasta valoare stocul e "limitat" (marcat cu rosu)
PROD_PER_PAG = 6  # Lab 4: produse pe pagina implicit (divizibil cu 1, 2 si 3 coloane, pentru Lab 5)
