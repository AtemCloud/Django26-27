"""Functiile de vizualizare ale aplicatiei magazin, impartite pe laboratoare:

  Lab 1/2  - clasa Accesare, pagina principala, /info, /log, /accesare<id>, despre, istoric, in lucru
  Lab 4/5  - lista de produse, paginile categoriilor, pagina produsului, filtrare, adaugare produs
  Lab 5    - pagina de contact si /mesaje (mesajele salvate in fisiere JSON)
  Lab 6    - inregistrare, login, logout, profil, modificarea datelor, schimbarea parolei
"""
import json
import os
import re
import time
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.messages import get_messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.text import slugify

from .forms import (COLOANE_SORTARE, ContactForm, CustomAuthenticationForm, CustomPasswordChangeForm,
                    CustomUserCreationForm, EditareContForm, EditareProfilForm, FiltruProduseForm, ProdusForm)
from .models import ArticolBlog, Categorie, Departament, Produs, Profil, TipMesaj
from .validators import varsta_ani_luni

# =============================================================================
# Lab 1/2: clasa Accesare (cerinta: "Creati o clasa numita Accesare (deocamdata in views.py)")
# =============================================================================

ZILE = ["Luni", "Marti", "Miercuri", "Joi", "Vineri", "Sambata", "Duminica"]
LUNI = ["", "Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie", "Iulie",
        "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie"]

FORMAT_IMPLICIT = "%A, %d %B %Y"  # de exemplu: Joi, 2 Octombrie 2025
PREFIX_APLICATIE = "/magazin"

ACCESARI = []  # lista cu toate accesarile de cand a pornit serverul (folosita de /log)


def formateaza_data_ro(data, format=FORMAT_IMPLICIT):
    """Ca strftime, dar cu numele zilelor si lunilor in limba romana.
    Scrisa o singura data si refolosita de Accesare (ca sa nu avem acelasi cod in 2 locuri)."""
    format = format.replace("%A", ZILE[data.weekday()])
    format = format.replace("%B", LUNI[data.month])
    format = format.replace("%d", str(data.day))
    return data.strftime(format)


class Accesare:
    """O instanta pentru fiecare cerere catre o pagina (creata in middleware.py)."""

    nr_accesari = 0  # contor comun pentru toate instantele, ca id-ul sa se autoincrementeze

    def __init__(self, ip_client, url, parametri=None, data=None):
        Accesare.nr_accesari += 1
        self.id = Accesare.nr_accesari
        self.ip_client = ip_client
        self.url = url
        self.parametri = parametri if parametri is not None else {}  # implicit un dictionar vid
        self.data = data if data is not None else datetime.now()  # momentul crearii obiectului

    def lista_parametri(self):
        """Lista de tupluri (nume_parametru, valoare); valoarea e None daca parametrul nu e setat."""
        lista = []
        for nume, valori in self.parametri.items():
            if not isinstance(valori, list):
                valori = [valori]
            for valoare in valori:
                lista.append((nume, valoare if valoare != "" else None))
        return lista

    def string_url(self):
        """Tot url-ul, impreuna cu query string-ul."""
        if not self.parametri:
            return self.url
        query = "&".join(f"{nume}={valoare if valoare is not None else ''}" for nume, valoare in self.lista_parametri())
        return f"{self.url}?{query}"

    def pagina(self):
        """Doar numele paginii din aplicatie, fara domeniu sau parametri (de exemplu / sau /info)."""
        pagina = self.url
        if pagina.startswith(PREFIX_APLICATIE):
            pagina = pagina[len(PREFIX_APLICATIE):]
        return pagina.rstrip("/") or "/"

    def data_formatata(self, format=FORMAT_IMPLICIT):
        return formateaza_data_ro(self.data, format)

    def calculeaza_data(self, format=FORMAT_IMPLICIT, tip=""):
        """Returneaza HTML-ul sectiunii "Data si ora". tip: "" (data si ora), "zi" (doar data) sau "timp" (doar ora)."""
        if tip == "zi":
            continut = self.data_formatata(format)
        elif tip == "timp":
            continut = self.data.strftime("%H:%M:%S")
        else:
            continut = f"{self.data_formatata(format)}, {self.data.strftime('%H:%M:%S')}"
        return f"<section><h2>Data și ora</h2><p>{continut}</p></section>"

    def proprietati(self):
        """Folosit de /log?tabel=... si de /accesare<id>: numele coloanelor si valorile lor."""
        return {
            "id": self.id,
            "ip_client": self.ip_client,
            "url": self.string_url(),
            "pagina": self.pagina(),
            "data": f"{self.data_formatata()} {self.data.strftime('%H:%M:%S')}",
            "parametri": self.lista_parametri(),
        }

    def __str__(self):
        # "camp: valoare" pentru fiecare metoda de mai sus; afisat in consola la fiecare cerere
        return (
            f"id: {self.id}\n"
            f"ip_client: {self.ip_client}\n"
            f"string_url: {self.string_url()}\n"
            f"pagina: {self.pagina()}\n"
            f"calculeaza_data: {self.data_formatata()} {self.data.strftime('%H:%M:%S')}\n"
            f"lista_parametri: {self.lista_parametri()}"
        )


# =============================================================================
# Lab 1/2: paginile simple
# =============================================================================


def index(request):
    # Lab 2: pagina principala (minim 3 sectiuni), extinde baza.html
    return render(request, "magazin/index.html", {
        "noutati": Produs.objects.select_related("categorie").order_by("-data_lansare")[:3],
        "articole": ArticolBlog.objects.all()[:3],
    })


def despre(request):
    return render(request, "magazin/despre.html")  # Lab 2: minim 2 sectiuni si o imagine din static


def istoric(request):
    return render(request, "magazin/istoric.html")


def in_lucru(request, titlu="Pagina"):
    # Lab 2: paginile din meniu care nu sunt inca implementate randeaza in_lucru.html
    return render(request, "magazin/in_lucru.html", {"pagina_titlu": titlu})


def eroare_404(request, exception=None):
    # Lab 4: pagina de eroare (de exemplu cand se cere un produs inexistent); vizibila cu DEBUG = False
    return render(request, "magazin/404.html", status=404)


def info(request):
    """Lab 1: /info cu sectiunea "Data si ora". ?data=zi -> doar data, ?data=timp -> doar ora.
    request.acces este obiectul Accesare creat de middleware pentru cererea curenta."""
    tip = request.GET.get("data", "")
    if tip not in ("zi", "timp"):
        tip = ""
    sectiune = mark_safe(request.acces.calculeaza_data(tip=tip))
    return render(request, "magazin/info.html", {"sectiune_data": sectiune})


COLOANE_LOG = ["id", "ip_client", "url", "pagina", "data", "parametri"]


def log(request):
    """Lab 2 Task 1: /log. Parametrii acceptati (se pot combina):
      ultimele=n            ultimele n accesari (eroare daca n nu e intreg sau e prea mare)
      accesari=nr|detalii   numarul de accesari / lista cu data si ora fiecarei accesari
      iduri=2,3&iduri=5     doar accesarile cu aceste id-uri, in ordine; dubluri=true pastreaza repetarile
      tabel=tot|id,url      tabel HTML cu toate coloanele sau doar cu cele cerute
    In plus: sectiunea "Parametri" si paginile cea mai accesata / cea mai putin accesata."""
    erori = []
    context = {}
    accesari = list(ACCESARI)

    # --- iduri si dubluri
    if "iduri" in request.GET:
        dubluri = request.GET.get("dubluri", "false").lower() == "true"  # implicit false
        dupa_id = {a.id: a for a in ACCESARI}
        selectate = []
        vazute = []
        for grup in request.GET.getlist("iduri"):  # parametrul poate aparea de mai multe ori
            for bucata in grup.split(","):
                bucata = bucata.strip()
                if not bucata.isdigit():
                    erori.append(f"Id invalid: {bucata}")
                    continue
                id_accesare = int(bucata)
                if id_accesare not in dupa_id:
                    erori.append(f"Nu exista accesarea cu id-ul {id_accesare}")
                elif dubluri or id_accesare not in vazute:
                    selectate.append(dupa_id[id_accesare])
                    vazute.append(id_accesare)
        accesari = selectate

    # --- ultimele=n
    if "ultimele" in request.GET:
        valoare = request.GET.get("ultimele")
        try:
            n = int(valoare)
            if n < 0:
                raise ValueError
        except ValueError:
            erori.append(f"Parametrul ultimele trebuie sa fie un numar intreg pozitiv (primit: {valoare}).")
        else:
            if n > len(accesari):
                erori.append(f"Exista doar {len(accesari)} accesari fata de {n} accesari cerute")
            accesari = accesari[-n:] if n > 0 else []

    # --- accesari=nr / accesari=detalii
    mod = request.GET.get("accesari")
    if mod == "nr":
        context["numar_accesari"] = len(ACCESARI)
    elif mod == "detalii":
        context["detalii"] = True

    # --- tabel=tot / tabel=id,url
    if "tabel" in request.GET:
        valoare = request.GET.get("tabel")
        if valoare == "tot":
            coloane = COLOANE_LOG
        else:
            coloane = [c.strip() for c in valoare.split(",") if c.strip()]
        necunoscute = [c for c in coloane if c not in COLOANE_LOG]
        if necunoscute:
            erori.append(f"Coloane necunoscute: {', '.join(necunoscute)}")
        context["coloane_tabel"] = [c for c in coloane if c in COLOANE_LOG]
        context["randuri_tabel"] = [a.proprietati() for a in accesari]

    # --- pagina cea mai accesata si cea mai putin accesata
    frecventa = {}
    for a in ACCESARI:
        frecventa[a.pagina()] = frecventa.get(a.pagina(), 0) + 1
    if frecventa:
        context["cea_mai_accesata"] = max(frecventa.items(), key=lambda pereche: pereche[1])
        context["cea_mai_putin_accesata"] = min(frecventa.items(), key=lambda pereche: pereche[1])

    context["accesari"] = accesari
    context["erori"] = erori
    context["parametri"] = list(request.GET.keys())
    return render(request, "magazin/log.html", context)


def accesare_detaliu(request, id):
    # Lab 2: ruta /accesare[id] (re_path in urls.py) afiseaza toate informatiile despre o accesare
    for a in ACCESARI:
        if a.id == int(id):
            return render(request, "magazin/accesare.html", {"a": a, "proprietati": a.proprietati()})
    raise Http404("Accesarea nu exista")


# =============================================================================
# Lab 4/5: produse
# =============================================================================


def aplica_filtre(produse, date):
    """Lab 5 Task 2: cate un filtru pentru fiecare camp completat in formularul de filtrare."""
    if date.get("nume"):
        produse = produse.filter(nume__icontains=date["nume"])
    if date.get("descriere"):
        produse = produse.filter(descriere__icontains=date["descriere"])
    if date.get("pret_min") is not None:
        produse = produse.filter(pret_curent__gte=date["pret_min"])
    if date.get("pret_max") is not None:
        produse = produse.filter(pret_curent__lte=date["pret_max"])
    if date.get("stoc_min") is not None:
        produse = produse.filter(stoc_online__gte=date["stoc_min"])
    if date.get("consum_max") is not None:
        produse = produse.filter(Q(consum_w__lte=date["consum_max"]) | Q(consum_w__isnull=True))
    if date.get("stare"):
        produse = produse.filter(stare=date["stare"])
    if date.get("lansat_dupa"):
        produse = produse.filter(data_lansare__gte=date["lansat_dupa"])
    if date.get("lansat_inainte"):
        produse = produse.filter(data_lansare__lte=date["lansat_inainte"])
    if date.get("interfata"):
        # cautare in vectorul de interfete (ArrayField), fara diferenta intre litere mari si mici
        iduri = [p.id for p in produse if any(date["interfata"].lower() in i.lower() for i in p.interfete_conectare)]
        produse = produse.filter(id__in=iduri)
    if date.get("categorie"):
        produse = produse.filter(categorie=date["categorie"])
    if date.get("brand"):
        produse = produse.filter(brand=date["brand"])  # filtrul care implica un ForeignKey
    if date.get("serviciu"):
        produse = produse.filter(servicii=date["serviciu"])
    return produse


def afisare_produse(request, categorie=None):
    """Lab 4: "Cum puteti face sa refolositi codul?" - pagina cu toate produsele si paginile categoriilor
    apeleaza amandoua aceasta functie (pentru o categorie se transmite si parametrul categorie).
    Ordinea: filtre din formular (Lab 5) -> taguri (Lab 4) -> sortare (Lab 4) -> paginare (Lab 4)."""
    produse = Produs.objects.select_related("categorie", "brand")
    if categorie:
        produse = produse.filter(categorie=categorie)

    # --- Lab 5 Task 2: formularul de filtrare (forms.Form)
    are_filtre = any(camp in request.GET for camp in FiltruProduseForm.base_fields)
    if are_filtre:
        form = FiltruProduseForm(request.GET, categorie_fixa=categorie)
    else:
        form = FiltruProduseForm(categorie_fixa=categorie)
    pe_pagina = settings.PROD_PER_PAG
    coloane = 3
    if are_filtre:
        # verificare la server: categoria (camp ascuns, readonly) nu a fost modificata, de exemplu din developer tools
        if categorie and request.GET.get("categorie") not in (None, "", str(categorie.pk)):
            messages.error(request, "Categoria din formular a fost modificata. Se afiseaza doar produsele "
                                    f"din categoria {categorie.nume}.")
        if form.is_valid():
            date = dict(form.cleaned_data)
            if categorie:
                date["categorie"] = categorie
            produse = aplica_filtre(produse, date)
            pe_pagina = date.get("pe_pagina") or pe_pagina
            coloane = date.get("coloane") or coloane
        else:
            messages.error(request, "Filtrele contin erori. Corectati campurile marcate.")

    # Lab 5: daca utilizatorul a schimbat numarul de produse pe pagina, il avertizam
    # (numarul ales anterior e tinut in sesiune)
    pe_pagina_anterior = request.session.get("pe_pagina")
    if pe_pagina_anterior and pe_pagina_anterior != pe_pagina:
        messages.info(request, f"Se afiseaza acum cate {pe_pagina} produse pe pagina. In urma repaginarii e "
                               "posibil sa fi sarit peste unele produse sau sa le vedeti din nou pe cele deja vizualizate.")
    request.session["pe_pagina"] = pe_pagina

    # --- Lab 4: taguri active (?tag=gaming&tag=ddr5) -> doar produsele care contin TOATE tagurile
    taguri_active = request.GET.getlist("tag")
    if taguri_active:
        produse = produse.filter(taguri__contains=taguri_active)

    # --- Lab 4: sortare dupa o coloana (?coloana=pret_curent&sort=a sau sort=d)
    coloana = request.GET.get("coloana", "nume")
    if coloana not in COLOANE_SORTARE:
        coloana = "nume"
    sens = request.GET.get("sort", "a")
    if sens == "d":
        produse = produse.order_by("-" + coloana, "id")
    else:
        produse = produse.order_by(coloana, "id")

    total = produse.count()
    if total == 0:
        messages.warning(request, "Niciun produs nu corespunde criteriilor alese. Incercati alte filtre.")
    messages.debug(request, f"Interogare produse: {total} rezultate, sortare {coloana} {sens}, taguri {taguri_active}")

    # --- Lab 4: paginare pe produsele sortate (PROD_PER_PAG din settings.py sau valoarea aleasa in formular)
    nrPagina = request.GET.get("pagina", 1)
    paginator = Paginator(produse, pe_pagina)
    try:
        obPagina = paginator.page(nrPagina)
    except PageNotAnInteger:
        obPagina = paginator.page(1)
    except EmptyPage:
        obPagina = paginator.page(paginator.num_pages)
        messages.warning(request, "Nu mai sunt produse. S-a afisat ultima pagina.")

    context = {
        "form": form,
        "categorie": categorie,
        "pagina": obPagina,
        "total": total,
        "taguri_active": taguri_active,
        "coloane": coloane,
        "coloana": coloana,
        "sens": sens,
        "coloane_sortare": COLOANE_SORTARE,
        "stoc_min": settings.STOC_MIN,
    }
    # Lab 5 Task 2 bonus: cererile facute cu fetch (js/produse.js) primesc doar zona cu produse, ca JSON,
    # astfel incat pagina nu se mai reincarca
    if request.headers.get("X-Requested-With") == "fetch":
        html = render_to_string("magazin/_zona_produse.html", context, request)
        mesaje = [{"tip": m.tags, "text": str(m)} for m in get_messages(request)]
        return JsonResponse({"status": "success", "html": html, "mesaje": mesaje})
    return render(request, "magazin/produse.html", context)


def produse(request):
    # Lab 4: toate produsele (acelasi template ca paginile categoriilor)
    return afisare_produse(request)


def categorie(request, slug):
    # Lab 4: /categorii/<nume_categorie>; refoloseste afisare_produse, doar pentru produsele categoriei
    categ = get_object_or_404(Categorie, slug=slug)
    return afisare_produse(request, categorie=categ)


def produs_detaliu(request, id):
    # Lab 4: pagina proprie a produsului (url-ul vine din get_absolute_url); 404 daca nu exista
    produs = get_object_or_404(Produs.objects.select_related("categorie", "brand"), id=id)
    # Lab 4: K produse alese aleator din aceeasi categorie (K_PRODUSE_SIMILARE din settings.py)
    similare = (Produs.objects.filter(categorie=produs.categorie).exclude(id=produs.id)
                .order_by("?")[:settings.K_PRODUSE_SIMILARE])
    if produs.stoc_limitat and produs.stoc_online > 0:
        messages.warning(request, f"Mai sunt doar {produs.stoc_online} bucati in stoc!")  # Lab 5 Task 1
    return render(request, "magazin/produs.html", {"produs": produs, "similare": similare})


def adauga_produs(request):
    """Lab 5 Task 4: formularul ProdusForm (ModelForm) cu doua campuri aditionale pentru pret."""
    if request.method == "POST":
        form = ProdusForm(request.POST, request.FILES)
        if form.is_valid():
            # initial se salveaza cu commit=False, ca sa calculam coloanele lipsa din campurile aditionale
            produs = form.save(commit=False)
            pret_achizitie = form.cleaned_data["pret_achizitie"]
            adaos_procent = form.cleaned_data["adaos_procent"]
            produs.pret_curent = round(pret_achizitie * (100 + adaos_procent) / 100, 2)
            produs.taguri = form.cleaned_data["taguri_text"]
            produs.interfete_conectare = form.cleaned_data["interfete_text"]
            produs.slug = slugify(produs.nume)
            produs.save()
            form.save_m2m()  # relatia many-to-many (servicii) se salveaza dupa ce produsul are id
            messages.success(request, f"Produsul {produs.nume} a fost adaugat la pretul de "
                                      f"{str(produs.pret_curent).replace('.', ',')} lei.")
            return redirect(produs.get_absolute_url())
        else:
            messages.error(request, "Produsul nu a fost salvat. Verificati campurile marcate.")
    else:
        form = ProdusForm()
    return render(request, "magazin/adauga_produs.html", {"form": form})


# =============================================================================
# Lab 5 Task 3: pagina de contact (mesajele nu se salveaza in baza de date, ci in fisiere JSON)
# =============================================================================

FOLDER_MESAJE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Mesaje_nerezolvate")


def folder_departament(nume_departament):
    """Mesaje_nerezolvate/<departament>. Existenta folderului e verificata intr-un bloc try,
    iar daca nu exista, folderul se creeaza."""
    cale = os.path.join(FOLDER_MESAJE, nume_departament)
    try:
        os.listdir(cale)
    except FileNotFoundError:
        os.makedirs(cale)
    return cale


def text_varsta(data_nasterii):
    """In loc de data nasterii salvam varsta "X ani si Y luni". Refoloseste varsta_ani_luni din validators.py,
    aceeasi functie care verifica si ca expeditorul e major (fara copy-paste)."""
    ani, luni = varsta_ani_luni(data_nasterii)
    return f"{ani} ani și {luni} luni"


def majuscula_dupa_punct(text):
    """Litera de dupa ".", "?", "!" sau "..." devine litera mare."""
    text = re.sub(r"(\.\.\.|[.?!])(\s+)([^\W\d_])", lambda m: m.group(1) + m.group(2) + m.group(3).upper(), text)
    return text[:1].upper() + text[1:]


def mesaj_in_html(mesaj):
    """Fiecare linie devine un paragraf <p></p>; spatiile succesive se comaseaza intr-unul singur."""
    paragrafe = []
    for linie in mesaj.splitlines():
        linie = re.sub(r"\s+", " ", linie).strip()
        if linie:
            paragrafe.append(f"<p>{escape(majuscula_dupa_punct(linie))}</p>")
    return "".join(paragrafe)


def salveaza_mesaj(cleaned_data, tip, ip, imagini):
    """Salveaza mesajul in Mesaje_nerezolvate/<departament>/mesaj_<timestamp>[_urgent].json"""
    departament = cleaned_data["departament"]
    for nume_dep in Departament.objects.values_list("nume", flat=True):
        folder_departament(nume_dep)  # subfoldere pentru toate departamentele din baza de date
    folder = folder_departament(departament.nume)

    # urgent = numarul de zile de asteptare este exact minimul cerut de tipul mesajului
    urgent = cleaned_data["minim_zile_asteptare"] == tip.min_zile
    acum = datetime.now()
    timestamp = int(time.time())  # secunde de la 1 ianuarie 1970
    nume_fisier = f"mesaj_{timestamp}_urgent.json" if urgent else f"mesaj_{timestamp}.json"

    nume_imagini = []
    for i, imagine in enumerate(imagini, start=1):
        extensie = os.path.splitext(imagine.name)[1].lower()
        nume = f"mesaj_{timestamp}_img{i}{extensie}"
        with open(os.path.join(folder, nume), "wb") as f:
            for bucata in imagine.chunks():
                f.write(bucata)
        nume_imagini.append(nume)

    # toate campurile din formular, fara confirmarea e-mailului, plus ip-ul, data si ora sosirii
    date_mesaj = {
        "nume": cleaned_data["nume"],
        "prenume": cleaned_data["prenume"],
        "cnp": cleaned_data["cnp"],
        "varsta": text_varsta(cleaned_data["data_nasterii"]),
        "email": cleaned_data["email"],
        "telefon": cleaned_data["telefon"],
        "tip_mesaj": tip.cod,
        "departament": departament.nume,
        "subiect": cleaned_data["subiect"],
        "minim_zile_asteptare": cleaned_data["minim_zile_asteptare"],
        "mesaj": mesaj_in_html(cleaned_data["mesaj"]),
        "imagini": nume_imagini,
        "gdpr": cleaned_data["gdpr"],
        "cod_cerere": cleaned_data["cod_cerere"],
        "urgent": urgent,
        "ip": ip,
        "data_sosire": acum.strftime("%Y-%m-%d"),
        "ora_sosire": acum.strftime("%H:%M:%S"),
    }
    with open(os.path.join(folder, nume_fisier), "w", encoding="utf-8") as f:
        json.dump(date_mesaj, f, ensure_ascii=False, indent=4)
    return nume_fisier, urgent


def citeste_mesaje(departament, an=None, luna=None, zi=None):
    """Pentru /mesaje: mesajele unui departament, filtrate dupa an, an+luna sau an+luna+zi."""
    folder = os.path.join(FOLDER_MESAJE, departament)
    lista = []
    try:
        fisiere = sorted(os.listdir(folder), reverse=True)
    except FileNotFoundError:
        return lista
    prefix = ""  # de exemplu "2026", "2026-11" sau "2026-11-25"
    if an:
        prefix = str(an)
        if luna:
            prefix += f"-{luna:02d}"
            if zi:
                prefix += f"-{zi:02d}"
    for nume_fisier in fisiere:
        if not (nume_fisier.startswith("mesaj_") and nume_fisier.endswith(".json")):
            continue
        try:
            with open(os.path.join(folder, nume_fisier), "r", encoding="utf-8") as f:
                date_fis = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        if prefix and not date_fis.get("data_sosire", "").startswith(prefix):
            continue
        date_fis["_fisier"] = nume_fisier
        lista.append(date_fis)
    return lista


def contact_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST, request.FILES)  # request.FILES: cele 3 imagini optionale
        if form.is_valid():
            tip = form.tipuri[form.cleaned_data["tip_mesaj"]]
            imagini = []
            for i in (1, 2, 3):
                if form.cleaned_data.get(f"imagine{i}"):
                    imagini.append(form.cleaned_data[f"imagine{i}"])
            nume_fisier, urgent = salveaza_mesaj(form.cleaned_data, tip, request.ip_client, imagini)
            messages.success(request, "Mesajul a fost trimis. Va vom raspunde in cel mai scurt timp.")
            if urgent:
                messages.info(request, "Mesajul a fost marcat ca urgent.")
            messages.debug(request, f"Mesaj salvat in {nume_fisier}")
            return redirect("contact")
        else:
            messages.error(request, "Mesajul nu a fost trimis. Corectati erorile din formular.")
    else:
        form = ContactForm()
    return render(request, "magazin/contact.html", {"form": form})


def api_departamente(request):
    """Pentru dropdown-ul dinamic de departamente (js/contact.js):
    pentru fiecare tip de mesaj, departamentele care il pot primi (din baza de date)."""
    date = {}
    for tip in TipMesaj.objects.prefetch_related("departamente"):
        date[tip.cod] = {
            "min_zile": tip.min_zile,
            "departamente": [{"id": d.id, "nume": d.nume} for d in tip.departamente.all()],
        }
    return JsonResponse(date)


def mesaje(request):
    """/mesaje?departament=Comenzi&data=2026 (sau 2026-11, sau 2026-11-25).
    Template-ul parcurge toate cheile din JSON, deci afisarea nu depinde de numarul si numele campurilor."""
    departamente = list(Departament.objects.values_list("nume", flat=True))
    departament = request.GET.get("departament")
    data = request.GET.get("data", "")
    an = luna = zi = None
    if data:
        try:
            bucati = [int(x) for x in data.split("-")]
            an, luna, zi = (bucati + [None, None])[:3]
        except ValueError:
            messages.error(request, "Data trebuie sa fie de forma AAAA, AAAA-LL sau AAAA-LL-ZZ.")
    lista = []
    if departament:
        if departament not in departamente:
            messages.error(request, "Departament necunoscut.")
        else:
            lista = citeste_mesaje(departament, an, luna, zi)
            if not lista:
                messages.warning(request, "Nu exista mesaje pentru criteriile alese.")
    for m in lista:
        m["mesaj"] = mark_safe(m.get("mesaj", ""))  # mesajul a fost deja transformat in HTML la salvare
    return render(request, "magazin/mesaje.html", {
        "departamente": departamente,
        "departament": departament,
        "data": data,
        "lista": lista,
    })


# =============================================================================
# Lab 6: utilizatori
# =============================================================================


def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # UserCreationForm salveaza parola criptata
            # randul din Profil se creeaza DOAR daca utilizatorul a completat macar un camp de profil
            if form.profil_completat():
                Profil.objects.create(utilizator=user, **form.date_profil())
            messages.success(request, "Contul a fost creat. Te poti loga.")
            return redirect("login")
        else:
            messages.error(request, "Contul nu a fost creat. Verificati erorile din formular.")
    else:
        form = CustomUserCreationForm()
    return render(request, "magazin/inregistrare.html", {"form": form})


def date_sesiune(user):
    """Datele utilizatorului (si ale profilului, daca exista) care se memoreaza in sesiune."""
    date = {
        "username": user.username,
        "nume": user.last_name,
        "prenume": user.first_name,
        "email": user.email,
        "telefon": user.telefon,
        "data_nasterii": user.data_nasterii.isoformat() if user.data_nasterii else None,
        "oras": user.oras,
        "profil": None,
    }
    profil = Profil.objects.filter(utilizator=user).first()
    if profil:
        date["profil"] = {
            "judet": profil.judet,
            "strada": profil.strada,
            "cod_postal": profil.cod_postal,
            "newsletter": profil.newsletter,
        }
    return date


def custom_login_view(request):
    if request.method == "POST":
        form = CustomAuthenticationForm(data=request.POST, request=request)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if not form.cleaned_data.get("ramane_logat"):
                request.session.set_expiry(0)  # sesiunea expira la inchiderea browserului
            else:
                request.session.set_expiry(24 * 60 * 60)  # o zi, in secunde
            # datele se memoreaza in sesiune; pagina de profil le citeste de acolo
            request.session["date_utilizator"] = date_sesiune(user)
            messages.success(request, f"Bine ai revenit, {user.first_name or user.username}!")
            return redirect("profil")  # redirectionare spre pagina cu datele lui
        else:
            messages.error(request, "Logarea a esuat.")
    else:
        form = CustomAuthenticationForm()
    return render(request, "magazin/login.html", {"form": form})


def logout_view(request):
    # linkul de logout apare in meniu doar pentru utilizatorii logati (baza.html)
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, "Te-ai delogat cu succes.")
    return redirect("index")


@login_required
def profil(request):
    if "date_utilizator" not in request.session:
        request.session["date_utilizator"] = date_sesiune(request.user)
    return render(request, "magazin/profil.html", {"date": request.session["date_utilizator"]})


@login_required
def editare_profil(request):
    """Modificarea datelor din Utilizator si din Profil.
    Daca utilizatorul nu are inca rand in Profil, se creeaza acum (doar daca a completat ceva)."""
    profil_existent = Profil.objects.filter(utilizator=request.user).first()
    if request.method == "POST":
        form_cont = EditareContForm(request.POST, instance=request.user)
        form_profil = EditareProfilForm(request.POST, instance=profil_existent)
        if form_cont.is_valid() and form_profil.is_valid():
            form_cont.save()
            if profil_existent or any(form_profil.cleaned_data.values()):
                profil = form_profil.save(commit=False)
                profil.utilizator = request.user
                profil.save()
            request.session["date_utilizator"] = date_sesiune(request.user)  # actualizam si datele din sesiune
            messages.success(request, "Datele au fost actualizate.")
            return redirect("profil")
        else:
            messages.error(request, "Datele nu au fost salvate. Verificati erorile.")
    else:
        form_cont = EditareContForm(instance=request.user)
        form_profil = EditareProfilForm(instance=profil_existent)
    return render(request, "magazin/editare_profil.html", {"form_cont": form_cont, "form_profil": form_profil})


@login_required
def change_password_view(request):
    if request.method == "POST":
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)  # utilizatorul ramane logat dupa schimbare
            messages.success(request, "Parola a fost actualizata.")
            return redirect("profil")
        else:
            messages.error(request, "Exista erori.")
    else:
        form = CustomPasswordChangeForm(user=request.user)
    return render(request, "magazin/schimba_parola.html", {"form": form})
