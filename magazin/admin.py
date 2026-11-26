"""Lab 4 Task admin. Unde e fiecare cerinta:
  - ordinea coloanelor schimbata: CategorieAdmin.fields
  - caracteristica dintr-un model legat (one-to-many): ProdusAdmin.tara_brand (tara brandului)
  - @admin.display + format_html: ProdusAdmin.pret_formatat, CategorieAdmin.culoare_vizual
  - search_fields pe 2 campuri + search_help_text: la fiecare model
  - ordonare dupa o coloana: ProdusAdmin.ordering (pret descrescator)
  - filtre laterale: ProdusAdmin.list_filter, BrandAdmin.list_filter
  - 5 elemente pe pagina: ProdusAdmin.list_per_page
  - sectiuni, una colapsabila: ProdusAdmin.fieldsets
  - titlu tab, antet, titlu pagina principala, "view site": admin.site.* mai jos
  - stilizare: templates/admin/base_site.html + static/magazin/css/admin_custom.css
  - minim 2 actiuni: ProdusAdmin.exporta_csv, exporta_json, marcheaza_resigilat
"""
import csv
import json

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponse
from django.utils.formats import number_format
from django.utils.html import format_html

from .models import (Angajat, ArticolBlog, Brand, Categorie, Comanda, ComandaProdus, Departament, Favorit,
                     IstoricPret, Produs, Profil, Review, ServiciuAditional, TipMesaj, Utilizator, Voucher)

# Lab 4: personalizarea site-ului de administrare
admin.site.site_title = "Admin Magazin Hardware"
admin.site.site_header = "Magazin Hardware - Administrare"
admin.site.index_title = "Gestionarea magazinului"
admin.site.site_url = "/magazin/"  # butonul "view site" duce la magazin


# ----------------------------------------------------------------- produse


class IstoricPretInline(admin.TabularInline):
    model = IstoricPret
    extra = 0


class ProdusAdmin(admin.ModelAdmin):
    # ordinea coloanelor schimbata fata de model + o coloana din modelul legat (brand)
    list_display = ["nume", "pret_formatat", "stoc_online", "categorie", "brand", "tara_brand", "stare"]
    list_filter = ["categorie", "brand", "stare", "data_lansare"]
    search_fields = ["nume", "descriere"]
    search_help_text = "Cautati dupa numele sau descrierea produsului (potrivire partiala)."
    ordering = ["-pret_curent"]
    list_per_page = 5
    prepopulated_fields = {"slug": ["nume"]}
    filter_horizontal = ["servicii"]
    inlines = [IstoricPretInline]
    actions = ["exporta_csv", "exporta_json", "marcheaza_resigilat"]
    fieldsets = [
        ("Date principale", {"fields": ["nume", "slug", "categorie", "brand", "pret_curent", "stoc_online", "stare"]}),
        ("Detalii tehnice (optional)", {
            "classes": ["collapse"],
            "fields": ["descriere", "consum_w", "data_lansare", "interfete_conectare", "taguri", "imagine", "servicii"],
        }),
    ]

    @admin.display(description="Pret", ordering="pret_curent")
    def pret_formatat(self, obj):
        culoare = "#c53030" if obj.pret_curent > 2000 else "#2f855a"
        # number_format: virgula zecimala, ca in magazin (1899,00 lei)
        return format_html('<b style="color:{}"><i>{} lei</i></b>', culoare, number_format(obj.pret_curent, 2))

    @admin.display(description="Tara brand", ordering="brand__tara_origine")
    def tara_brand(self, obj):
        return obj.brand.tara_origine

    @admin.action(description="Exporta produsele selectate in CSV")
    def exporta_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="produse.csv"'
        response.write("﻿")  # ca Excel sa recunoasca diacriticele
        writer = csv.writer(response)
        writer.writerow(["id", "nume", "categorie", "brand", "pret", "stoc", "stare", "taguri"])
        for p in queryset.select_related("categorie", "brand"):
            writer.writerow([p.id, p.nume, p.categorie, p.brand.nume, p.pret_curent, p.stoc_online, p.stare,
                             ";".join(p.taguri)])
        return response

    @admin.action(description="Exporta produsele selectate in JSON")
    def exporta_json(self, request, queryset):
        date = [{"id": p.id, "nume": p.nume, "categorie": p.categorie.nume, "pret": str(p.pret_curent),
                 "stoc": p.stoc_online, "taguri": p.taguri} for p in queryset.select_related("categorie")]
        response = HttpResponse(json.dumps(date, ensure_ascii=False, indent=2), content_type="application/json")
        response["Content-Disposition"] = 'attachment; filename="produse.json"'
        return response

    @admin.action(description="Marcheaza ca resigilate")
    def marcheaza_resigilat(self, request, queryset):
        nr = queryset.exclude(stare="precomanda").update(stare=Produs.Stare.RESIGILAT)
        self.message_user(request, f"{nr} produse marcate ca resigilate.", messages.SUCCESS)


admin.site.register(Produs, ProdusAdmin)


class CategorieAdmin(admin.ModelAdmin):
    fields = ["nume", "slug", "culoare", "sigla", "afisata_in_meniu", "descriere"]  # ordine schimbata
    list_display = ["nume", "culoare_vizual", "afisata_in_meniu"]
    search_fields = ["nume", "descriere"]
    search_help_text = "Cautati dupa nume sau descriere."
    prepopulated_fields = {"slug": ["nume"]}

    @admin.display(description="Culoare")
    def culoare_vizual(self, obj):
        return format_html('<span style="background:{0};color:#fff;padding:2px 8px;border-radius:3px">{0}</span>',
                           obj.culoare)


admin.site.register(Categorie, CategorieAdmin)


class BrandAdmin(admin.ModelAdmin):
    list_display = ["nume", "tara_origine", "url_suport_drivere"]
    search_fields = ["nume", "tara_origine"]
    search_help_text = "Cautati dupa numele brandului sau tara de origine."
    list_filter = ["tara_origine"]


admin.site.register(Brand, BrandAdmin)


class ServiciuAdmin(admin.ModelAdmin):
    list_display = ["nume", "tarif", "disponibil_online"]
    search_fields = ["nume", "tarif"]
    search_help_text = "Cautati dupa nume sau tarif."


admin.site.register(ServiciuAditional, ServiciuAdmin)


class IstoricPretAdmin(admin.ModelAdmin):
    list_display = ["produs", "nr_modificare", "valoare_pret", "data_aplicare"]
    search_fields = ["produs__nume", "valoare_pret"]
    search_help_text = "Cautati dupa numele produsului sau valoarea pretului."


admin.site.register(IstoricPret, IstoricPretAdmin)


class ArticolBlogAdmin(admin.ModelAdmin):
    list_display = ["titlu", "data_publicarii"]
    search_fields = ["titlu", "continut"]
    search_help_text = "Cautati in titlu sau continut."
    filter_horizontal = ["produse"]


admin.site.register(ArticolBlog, ArticolBlogAdmin)


# ----------------------------------------------------------------- contact, utilizatori, comenzi


class DepartamentAdmin(admin.ModelAdmin):
    list_display = ["nume", "email", "sef"]
    search_fields = ["nume", "email"]
    search_help_text = "Cautati dupa nume sau e-mail."


admin.site.register(Departament, DepartamentAdmin)


class TipMesajAdmin(admin.ModelAdmin):
    list_display = ["nume", "cod", "min_zile"]
    search_fields = ["nume", "cod"]
    search_help_text = "Cautati dupa nume sau cod."
    filter_horizontal = ["departamente"]


admin.site.register(TipMesaj, TipMesajAdmin)


class ProfilInline(admin.StackedInline):
    model = Profil
    can_delete = False


class UtilizatorAdmin(UserAdmin):
    """Lab 6: utilizatorul personalizat, cu campurile suplimentare si Profilul in aceeasi pagina."""
    list_display = ["username", "email", "first_name", "last_name", "oras", "is_staff"]
    search_fields = ["username", "email"]
    search_help_text = "Cautati dupa username sau e-mail."
    inlines = [ProfilInline]
    fieldsets = UserAdmin.fieldsets + (
        ("Date suplimentare", {"fields": ["telefon", "data_nasterii", "oras"]}),
    )


admin.site.register(Utilizator, UtilizatorAdmin)


class AngajatAdmin(admin.ModelAdmin):
    list_display = ["utilizator", "departament", "functie", "data_angajare"]
    search_fields = ["utilizator__username", "functie"]
    search_help_text = "Cautati dupa username sau functie."


admin.site.register(Angajat, AngajatAdmin)


class ComandaProdusInline(admin.TabularInline):
    model = ComandaProdus
    extra = 1


class ComandaAdmin(admin.ModelAdmin):
    list_display = ["id", "utilizator", "data_plasarii", "status", "prin_curier"]
    list_filter = ["status", "prin_curier"]
    search_fields = ["utilizator__username", "adresa_livrare"]
    search_help_text = "Cautati dupa username sau adresa de livrare."
    inlines = [ComandaProdusInline]


admin.site.register(Comanda, ComandaAdmin)


class ReviewAdmin(admin.ModelAdmin):
    list_display = ("produs", "utilizator", "rating", "data")
    search_fields = ("produs__nume", "text")
    search_help_text = "Cautati dupa numele produsului sau textul review-ului."


admin.site.register(Review, ReviewAdmin)


class FavoritAdmin(admin.ModelAdmin):
    search_fields = ("produs__nume", "utilizator__username")
    search_help_text = "Cautati dupa numele produsului sau username."


admin.site.register(Favorit, FavoritAdmin)


class VoucherAdmin(admin.ModelAdmin):
    search_fields = ("cod", "utilizator__username")
    search_help_text = "Cautati dupa codul voucherului sau username."


admin.site.register(Voucher, VoucherAdmin)


class ProfilAdmin(admin.ModelAdmin):
    search_fields = ("utilizator__username", "judet")
    search_help_text = "Cautati dupa username sau judet."


admin.site.register(Profil, ProfilAdmin)
