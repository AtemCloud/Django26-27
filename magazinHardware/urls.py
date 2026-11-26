from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("magazin/", include("magazin.urls")),
    path("", RedirectView.as_view(url="/magazin/", permanent=False)),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler404 = "magazin.views.eroare_404"  # Lab 4: pagina de eroare pentru produs inexistent
