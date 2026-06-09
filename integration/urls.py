from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.integration.views.job_platform_view import (
    DropIntegrationView,
    InitializeHandshakeView,
    TokenExchangeView,
    ErpUserLookupProxyView,
)

router = DefaultRouter(trailing_slash=False)

urlpatterns = [
    path(
        "v1/",
        include(
            [
                path("integration/initialize", InitializeHandshakeView.as_view()),
                path("integration/exchange", TokenExchangeView.as_view()),
                path("integration/look_up/users", ErpUserLookupProxyView.as_view()),
                path("integration/disconnect", DropIntegrationView.as_view()),
            ]
        ),
    ),
    path("", include(router.urls)),
]
