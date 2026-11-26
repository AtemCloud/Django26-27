"""Rutele aplicatiei. Sunt incluse in magazinHardware/urls.py sub prefixul /magazin/.
In template-uri linkurile se genereaza cu {% url 'nume_ruta' %}, iar in views cu redirect('nume_ruta')."""
from django.urls import path, re_path

from . import views

urlpatterns = [
    # ---- Lab 1/2
    path("", views.index, name="index"),
    path("info/", views.info, name="info"),
    path("log/", views.log, name="log"),
    re_path(r"^accesare(?P<id>\d+)/?$", views.accesare_detaliu, name="accesare"),  # Lab 2: /accesare[id]
    path("despre/", views.despre, name="despre"),
    path("istoric/", views.istoric, name="istoric"),
    path("cos_virtual/", views.in_lucru, {"titlu": "Cos virtual"}, name="cos_virtual"),  # Lab 2: pagina "in lucru"
    # ---- Lab 4/5: produse
    path("produse/", views.produse, name="produse"),
    path("produse/adauga/", views.adauga_produs, name="adauga_produs"),  # Lab 5 Task 4
    path("produs/<int:id>/", views.produs_detaliu, name="produs"),
    path("categorii/<slug:slug>/", views.categorie, name="categorie"),
    # ---- Lab 5 Task 3: contact
    path("contact/", views.contact_view, name="contact"),
    path("mesaje/", views.mesaje, name="mesaje"),
    path("api/departamente/", views.api_departamente, name="api_departamente"),
    # ---- Lab 6: utilizatori
    path("inregistrare/", views.register_view, name="inregistrare"),
    path("login/", views.custom_login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profil/", views.profil, name="profil"),
    path("profil/editare/", views.editare_profil, name="editare_profil"),
    path("profil/parola/", views.change_password_view, name="schimba_parola"),
]
