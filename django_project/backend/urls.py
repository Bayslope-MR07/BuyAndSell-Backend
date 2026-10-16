from django.contrib import admin
from django.urls import include, path, re_path
from django.conf.urls.static import static
from django.views.static import serve
from django.views.generic import TemplateView
from backend import settings
from accounts.views.googleLogin import GoogleLogin
# from accounts.views.views import login_test
from accounts.views.views import login_test, debug_login_mapping
from django.http import JsonResponse

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/accounts/login/", login_test, name="login_direct"),
    path("api/accounts/", include("accounts.urls")),
    path("api/v1/auth/google/", GoogleLogin.as_view(), name="google_login"),
    path("api/debug-login/", debug_login_mapping),
]

# ==== Media files serving ====
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]

# ==== Angular catch-all ====
urlpatterns += [
    # re_path(r'^(?!api/|media/).*$', TemplateView.as_view(template_name='index.html')),
    # health check for API Gateway
    path("", lambda request: JsonResponse({"status": "ok"})),
    # Angular catch-all (but NOT root)
    re_path(r"^(?!$|api/|media/).*$", TemplateView.as_view(template_name="index.html")),
]
