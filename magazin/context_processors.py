from django.conf import settings
from django.db.models import Count

from .models import Categorie


def date_firma(request):
    """Lab 2: datele firmei (din settings.py) disponibile in toate template-urile (footer)."""
    return {"firma": settings.DATE_FIRMA}


def categorii_meniu(request):
    """Lab 4: meniul de categorii generat din baza de date (doar categoriile cu produse)."""
    return {
        "categorii_meniu": Categorie.objects.filter(afisata_in_meniu=True)
        .annotate(nr_produse=Count("produse"))
        .filter(nr_produse__gt=0)
    }

