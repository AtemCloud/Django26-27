"""python manage.py seed_date  -> populeaza baza de date cu date de test (idempotent).

Produsele (nume, specificatii, data lansarii) sunt in produse.json, langa acest fisier; specificatiile sunt
luate de pe paginile oficiale ale producatorilor. Pozele sunt in media/produse/<slug>.jpg (surse: media/produse/SURSE.md).
"""
import datetime
import json
import random
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from magazin.models import (ArticolBlog, Brand, Categorie, Departament, IstoricPret, Produs,
                            ServiciuAditional, TipMesaj)

CATEGORII = [
    ("Procesoare", "Procesoare desktop pentru gaming si productivitate.", "#c53030", "fa-solid fa-microchip"),
    ("Placi video", "Placi grafice dedicate pentru gaming, randare si AI.", "#2f855a", "fa-solid fa-display"),
    ("Memorii RAM", "Module DDR4 si DDR5 pentru desktop.", "#6b46c1", "fa-solid fa-memory"),
    ("Stocare", "SSD-uri NVMe, SATA si hard disk-uri.", "#2b6cb0", "fa-solid fa-hard-drive"),
    ("Placi de baza", "Placi de baza pentru platformele Intel si AMD.", "#b7791f", "fa-solid fa-server"),
    ("Surse", "Surse de alimentare certificate 80+.", "#4a5568", "fa-solid fa-plug"),
    ("Periferice", "Tastaturi, mouse-uri si casti.", "#d53f8c", "fa-solid fa-keyboard"),
    ("Racire", "Categorie fara produse, pentru testarea meniului.", "#319795", "fa-solid fa-fan"),
]

BRANDURI = [
    ("AMD", "SUA", "https://www.amd.com/en/support"),
    ("Intel", "SUA", "https://www.intel.com/content/www/us/en/download-center/home.html"),
    ("NVIDIA", "SUA", "https://www.nvidia.com/Download/index.aspx"),
    ("ASUS", "Taiwan", "https://www.asus.com/support/"),
    ("MSI", "Taiwan", "https://www.msi.com/support"),
    ("Corsair", "SUA", "https://www.corsair.com/downloads"),
    ("Kingston", "SUA", "https://www.kingston.com/support"),
    ("Samsung", "Coreea de Sud", "https://semiconductor.samsung.com/consumer-storage/support/tools/"),
    ("Logitech", "Elvetia", "https://support.logi.com/"),
    ("Seasonic", "Taiwan", None),
]

SERVICII = [
    ("Montaj in sistem", Decimal("49.99"), True),
    ("Extindere garantie 12 luni", Decimal("99.00"), True),
    ("Testare si burn-in 24h", Decimal("79.00"), False),
    ("Livrare express", Decimal("29.99"), True),
    ("Configurare BIOS si drivere", Decimal("59.00"), False),
]

PRODUSE = json.loads((Path(__file__).with_name("produse.json")).read_text(encoding="utf-8"))

DEPARTAMENTE = ["Administratie", "Relatii clienti", "Comenzi", "Service si garantii", "Calitate (QA)", "Resurse umane"]

# tip: (nume, min_zile, departamente)
TIPURI_MESAJE = {
    "reclamatie": ("Reclamatie", 2, ["Relatii clienti", "Service si garantii", "Administratie"]),
    "intrebare": ("Intrebare", 2, ["Relatii clienti", "Comenzi"]),
    "review": ("Review", 4, ["Calitate (QA)", "Administratie"]),
    "cerere": ("Cerere", 4, ["Resurse umane", "Administratie", "Comenzi"]),
    "programare": ("Programare", 3, ["Service si garantii", "Relatii clienti"]),
}

ARTICOLE = [
    ("Cum alegi placa video in 2026", "Ghid pentru 1080p, 1440p si 4K.", ["placi video"]),
    ("DDR4 sau DDR5?", "Diferentele practice pentru gaming si productivitate.", ["memorii ram"]),
    ("Ce sursa iti trebuie", "Calculam consumul real al unui sistem.", ["surse"]),
    ("NVMe vs SATA", "Merita un SSD NVMe pentru gaming?", ["stocare"]),
    ("Primul tau PC de gaming", "Configuratii recomandate pe trei bugete.", ["procesoare", "placi video"]),
]


class Command(BaseCommand):
    help = "Populeaza baza de date cu date de test."

    @transaction.atomic
    def handle(self, *args, **opts):
        rnd = random.Random(42)
        categorii = {}
        for i, (nume, descr, culoare, sigla) in enumerate(CATEGORII):
            categorii[nume], _ = Categorie.objects.update_or_create(
                nume=nume, defaults=dict(slug=slugify(nume), descriere=descr, culoare=culoare, sigla=sigla))
        branduri = {}
        for nume, tara, url in BRANDURI:
            branduri[nume], _ = Brand.objects.update_or_create(
                nume=nume, defaults=dict(tara_origine=tara, url_suport_drivere=url))
        servicii = [ServiciuAditional.objects.update_or_create(nume=n, defaults=dict(tarif=t, disponibil_online=d))[0]
                    for n, t, d in SERVICII]

        produse = []
        for date in PRODUSE:
            nume_complet = f"{date['brand']} {date['nume']}"
            slug = slugify(nume_complet)
            # produsele redenumite (nume mai exact) isi pastreaza id-ul, istoricul si legaturile
            if date.get("slug_vechi") and not Produs.objects.filter(slug=slug).exists():
                Produs.objects.filter(slug=date["slug_vechi"]).update(slug=slug)
            stare = rnd.choices(["nou", "resigilat", "precomanda", "reconditionat"], [70, 12, 8, 10])[0]
            stoc = 0 if stare == "precomanda" else rnd.choice([0, 1, 2, 3, 4, 6, 8, 12, 15, 25, 40])
            an, luna = map(int, date["lansare"].split("-"))
            produs, _ = Produs.objects.update_or_create(
                slug=slug,
                defaults=dict(
                    nume=nume_complet, pret_curent=Decimal(date["pret"]), consum_w=date["consum_w"],
                    interfete_conectare=date["interfete"], taguri=date["taguri"], stare=stare, stoc_online=stoc,
                    categorie=categorii[date["categorie"]], brand=branduri[date["brand"]],
                    data_lansare=datetime.date(an, luna, 1),  # se afiseaza doar luna si anul
                    descriere=date["descriere"],
                ))
            # poza reala, daca exista; altfel camp gol, iar site-ul arata imaginea "indisponibila"
            poza = f"produse/{slug}.jpg" if (Path(settings.MEDIA_ROOT) / "produse" / f"{slug}.jpg").exists() else ""
            if produs.imagine.name != poza:
                produs.imagine = poza
                produs.save(update_fields=["imagine"])
            produs.servicii.set(rnd.sample(servicii, rnd.randint(0, 3)))
            produse.append(produs)
            if not produs.istoric_preturi.exists():
                pret_vechi = Decimal(date["pret"]) * Decimal("1.15")
                for nr in range(1, rnd.randint(2, 4)):
                    IstoricPret.objects.create(produs=produs, nr_modificare=nr, valoare_pret=round(pret_vechi, 2),
                                               data_aplicare=datetime.date.today() - datetime.timedelta(days=200 - 60 * nr))
                    pret_vechi *= Decimal("0.95")

        for titlu, continut, categ_legate in ARTICOLE:
            art, _ = ArticolBlog.objects.update_or_create(titlu=titlu, defaults=dict(continut=continut))
            art.produse.set([p for p in produse if p.categorie.nume.lower() in categ_legate][:5])

        departamente = {n: Departament.objects.get_or_create(nume=n, defaults={
            "email": f"{slugify(n)}@magazinhardware.ro"})[0] for n in DEPARTAMENTE}
        for cod, (nume, min_zile, deps) in TIPURI_MESAJE.items():
            tip, _ = TipMesaj.objects.update_or_create(cod=cod, defaults=dict(nume=nume, min_zile=min_zile))
            tip.departamente.set([departamente[d] for d in deps])

        self.stdout.write(self.style.SUCCESS(
            f"OK: {Categorie.objects.count()} categorii, {Brand.objects.count()} branduri, "
            f"{Produs.objects.count()} produse, {IstoricPret.objects.count()} preturi istorice, "
            f"{TipMesaj.objects.count()} tipuri de mesaje."))
