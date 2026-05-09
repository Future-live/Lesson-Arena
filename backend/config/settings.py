import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import unquote, urlparse


BASE_DIR = Path(__file__).resolve().parent.parent


def env_path(name: str, default: Path) -> Path:
    value = os.getenv(name)
    if not value:
        return default
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


def ensure_mysql_driver() -> None:
    import pymysql

    pymysql.install_as_MySQLdb()


def database_config_from_url(url: str) -> dict:
    parsed = urlparse(url)
    scheme = parsed.scheme.split("+", 1)[0].lower()

    if scheme in {"postgres", "postgresql"}:
        engine = "django.db.backends.postgresql"
        default_port = "5432"
    elif scheme in {"mysql", "mariadb"}:
        ensure_mysql_driver()
        engine = "django.db.backends.mysql"
        default_port = "3306"
    else:
        raise ValueError(f"Unsupported DATABASE_URL scheme: {parsed.scheme}")

    config = {
        "ENGINE": engine,
        "NAME": unquote(parsed.path.lstrip("/")),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or default_port),
    }
    if engine == "django.db.backends.mysql":
        config["OPTIONS"] = {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    return config


SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-replace-me-before-production-lesson-plan-review-system",
)
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "127.0.0.1,localhost,testserver")
CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1,http://localhost",
)
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://127.0.0.1:5173,http://localhost:5173",
)
CORS_ALLOWED_ORIGIN_REGEXES = env_list(
    "CORS_ALLOWED_ORIGIN_REGEXES",
    r"^http://127\.0\.0\.1:\d+$,^http://localhost:\d+$",
)
CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS", False)
CORS_ALLOW_CREDENTIALS = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "apps.core",
    "apps.accounts",
    "apps.lesson_plans",
    "apps.reviews",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if DATABASE_URL:
    DATABASES = {
        "default": database_config_from_url(DATABASE_URL),
    }
else:
    DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").lower()
    if DB_ENGINE in {"postgres", "postgresql"}:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": os.getenv("POSTGRES_DB", "lesson_review"),
                "USER": os.getenv("POSTGRES_USER", "postgres"),
                "PASSWORD": os.getenv("POSTGRES_PASSWORD", "postgres"),
                "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
                "PORT": os.getenv("POSTGRES_PORT", "5432"),
            }
        }
    elif DB_ENGINE in {"mysql", "mariadb"}:
        ensure_mysql_driver()
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.mysql",
                "NAME": os.getenv("MYSQL_DATABASE", os.getenv("MYSQL_DB", "lesson_review")),
                "USER": os.getenv("MYSQL_USER", "root"),
                "PASSWORD": os.getenv("MYSQL_PASSWORD", ""),
                "HOST": os.getenv("MYSQL_HOST", "127.0.0.1"),
                "PORT": os.getenv("MYSQL_PORT", "3306"),
                "OPTIONS": {
                    "charset": "utf8mb4",
                    "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
                },
            }
        }
    else:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }

DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["CONN_MAX_AGE"] = int(os.getenv("DB_CONN_MAX_AGE", "60"))
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Shanghai")
USE_I18N = True
USE_TZ = True

STATIC_URL = os.getenv("STATIC_URL", "/static/")
STATIC_ROOT = env_path("STATIC_ROOT", BASE_DIR / "staticfiles")
SERVE_STATIC_FILES = env_bool("SERVE_STATIC_FILES", False)

MEDIA_URL = os.getenv("MEDIA_URL", "/media/")
MEDIA_ROOT = env_path("MEDIA_ROOT", BASE_DIR / "media")
SERVE_MEDIA_FILES = env_bool("SERVE_MEDIA_FILES", True)
MEDIA_STORAGE_BACKEND = os.getenv("MEDIA_STORAGE_BACKEND", "django.core.files.storage.FileSystemStorage")

STORAGES = {
    "default": {
        "BACKEND": MEDIA_STORAGE_BACKEND,
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
STATICFILES_STORAGE = STORAGES["staticfiles"]["BACKEND"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "COERCE_DECIMAL_TO_STRING": False,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 12,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "30"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "教案评价系统 API",
    "DESCRIPTION": "支持双教案成组上传、文档解析、全员多维评价与统计分析的完整系统。",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_TASK_ALWAYS_EAGER", False)
CELERY_TASK_EAGER_PROPAGATES = True

MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".md", ".markdown"}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = os.getenv("X_FRAME_OPTIONS", "SAMEORIGIN")

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
}
