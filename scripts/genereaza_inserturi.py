"""Lab 4 (bonus): genereaza comenzi INSERT cu produse aleatoare dar valide (respecta constrangerile).

Folosire:  python scripts/genereaza_inserturi.py 50 > produse_generate.sql
Apoi rulati fisierul in pgAdmin. Id-urile de categorii si branduri se citesc din baza de date,
deci rulati scriptul din folderul proiectului (cu .env configurat).
"""
import os
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "magazinHardware.settings")
import django  # noqa: E402

django.setup()
from django.utils.text import slugify  # noqa: E402

from magazin.models import Brand, Categorie, Produs  # noqa: E402

MODELE = ["Nova", "Titan", "Vortex", "Pulse", "Zenith", "Aero", "Blaze", "Orion", "Strix", "Phantom"]
TAGURI = ["gaming", "buget", "rgb", "silentios", "overclock", "productivitate", "wireless", "ddr5", "ddr4", "4k"]
INTERFETE = ["PCIe 4.0 x16", "PCIe 5.0", "HDMI 2.1", "DisplayPort 1.4a", "USB-C", "SATA III", "M.2 2280", "AM5", "LGA1700"]


def sql(valoare):
    if valoare is None:
        return "NULL"
    if isinstance(valoare, bool):
        return "TRUE" if valoare else "FALSE"
    if isinstance(valoare, (int, float)):
        return str(valoare)
    if isinstance(valoare, list):
        return "ARRAY[" + ",".join(sql(v) for v in valoare) + "]::varchar(30)[]" if valoare else "'{}'"
    return "'" + str(valoare).replace("'", "''") + "'"


def main(n):
    categorii = list(Categorie.objects.values_list("id", "nume"))
    branduri = list(Brand.objects.values_list("id", "nume"))
    sluguri = set(Produs.objects.values_list("slug", flat=True))
    rnd = random.Random()
    print("-- produse generate automat")
    for _ in range(n):
        cid, cnume = rnd.choice(categorii)
        bid, bnume = rnd.choice(branduri)
        while True:
            nume = f"{bnume} {rnd.choice(MODELE)} {rnd.randint(100, 9999)}"
            slug = slugify(nume)
            if slug not in sluguri:  # slug unic
                sluguri.add(slug)
                break
        stare = rnd.choices(["nou", "resigilat", "precomanda", "reconditionat"], [70, 10, 10, 10])[0]
        stoc = 0 if stare == "precomanda" else rnd.randint(0, 50)  # constrangere precomanda -> stoc 0
        consum = rnd.choice([None, rnd.randint(5, 3000)])  # constrangere consum <= 3000
        pret = round(rnd.uniform(49, 9999), 2)  # constrangere pret > 0
        lansare = date(2015, 1, 1) + timedelta(days=rnd.randint(0, 4000))  # constrangere >= 1990
        valori = {
            "nume": nume, "slug": slug, "descriere": f"{nume}, produs din categoria {cnume.lower()}.",
            "pret_curent": pret, "stoc_online": stoc, "consum_w": consum, "stare": stare,
            "data_lansare": lansare.isoformat(), "interfete_conectare": rnd.sample(INTERFETE, rnd.randint(0, 3)),
            "taguri": rnd.sample(TAGURI, rnd.randint(1, 4)), "imagine": None, "data_adaugare": "now()",
            "categorie_id": cid, "brand_id": bid,
        }
        coloane = ", ".join(valori)
        valori_sql = ", ".join("now()" if v == "now()" else sql(v) for v in valori.values())
        print(f"INSERT INTO magazin_produs ({coloane}) VALUES ({valori_sql});")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 50)
