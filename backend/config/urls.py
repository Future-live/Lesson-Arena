from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from apps.core.media import serve_media_file

media_serve = xframe_options_exempt(serve_media_file)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/docs/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/batches/", include("apps.lesson_plans.urls")),
    path("api/reviews/", include("apps.reviews.urls")),
    path("api/system/", include("apps.core.urls")),
]

# CloudBase service paths may be forwarded with or without the configured
# prefix. Keep unprefixed API routes so /api/* works in either mode.
urlpatterns += [
    path("schema/", SpectacularAPIView.as_view(), name="schema-unprefixed"),
    path("docs/swagger/", SpectacularSwaggerView.as_view(url_name="schema-unprefixed"), name="swagger-ui-unprefixed"),
    path("docs/redoc/", SpectacularRedocView.as_view(url_name="schema-unprefixed"), name="redoc-unprefixed"),
    path("auth/", include("apps.accounts.urls")),
    path("batches/", include("apps.lesson_plans.urls")),
    path("reviews/", include("apps.reviews.urls")),
    path("system/", include("apps.core.urls")),
]

if settings.DEBUG or settings.SERVE_MEDIA_FILES:
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            media_serve,
        ),
        re_path(
            r"^api/media/(?P<path>.*)$",
            media_serve,
        ),
    ]

if settings.DEBUG or settings.SERVE_STATIC_FILES:
    urlpatterns += [
        re_path(
            r"^static/(?P<path>.*)$",
            serve,
            {"document_root": settings.STATIC_ROOT},
        ),
        re_path(
            r"^api/static/(?P<path>.*)$",
            serve,
            {"document_root": settings.STATIC_ROOT},
        ),
    ]
