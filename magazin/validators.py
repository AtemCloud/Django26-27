"""Functii de validare refolosite in mai multe formulare (Lab 5, Lab 6).
Fiind functii separate, le dam prin parametrul validators=[...] sau le apelam din clean_<camp>,
fara sa repetam codul. Marcajele (0.x) sunt punctajele din Lab 5 Task 3."""
import datetime
import random
import re
import string

from django.core.exceptions import ValidationError

# ----------------------------------------------------------------- texte / nume


def incepe_cu_majuscula(valoare):  # (0.2) aplicata pe nume, prenume si subiect
    """Textul incepe cu litera mare si contine doar litere, spatii si cratime."""
    if not valoare:
        return  # campurile optionale (prenumele) pot fi goale
    if not valoare[0].isupper():
        raise ValidationError("Textul trebuie sa inceapa cu litera mare.", code="fara_majuscula")
    if not re.fullmatch(r"[^\W\d_]+([ \-][^\W\d_]+)*[ \-]?", valoare) or "  " in valoare:
        raise ValidationError("Sunt permise doar litere, spatii si cratime.", code="caractere_invalide")


def majuscula_dupa_separator(valoare):  # (0.1) a doua functie pentru nume si prenume
    """Dupa spatiu sau cratima urmeaza litera mare (de ex. Ana-Maria, Ion Vasile)."""
    if not valoare:
        return
    for parte in re.split(r"[ \-]", valoare):
        if parte and not parte[0].isupper():
            raise ValidationError(
                "Dupa spatiu sau cratima trebuie sa urmeze o litera mare (de ex. Ana-Maria).",
                code="separator_fara_majuscula",
            )


CUVANT = re.compile(r"[^\W_]+")


def cuvinte(text):
    """Cuvintele sunt secvente alfanumerice separate prin secvente nealfanumerice."""
    return CUVANT.findall(text or "")


def fara_linkuri(valoare):  # (0.3, partea a doua) pentru mesaj si subiect
    for bucata in (valoare or "").split():
        if bucata.lower().startswith(("http://", "https://")):
            raise ValidationError("Textul nu poate contine linkuri.", code="link")
        if re.search(r"[^\W_]+\.[^\W_]+\.[^\W_]+", bucata):
            raise ValidationError(
                "Nu sunt permise siruri de forma cuvant1.cuvant2.cuvant3 (arata ca un link).", code="link_ascuns"
            )


# ----------------------------------------------------------------- varsta / CNP


def varsta_ani_luni(data_nasterii, azi=None):  # refolosita la validare SI la preprocesare
    """(ani, luni) impliniti. Folosita si la validare (majorat) si la preprocesare (varsta salvata)."""
    azi = azi or datetime.date.today()
    luni_total = (azi.year - data_nasterii.year) * 12 + (azi.month - data_nasterii.month)
    if azi.day < data_nasterii.day:
        luni_total -= 1
    return luni_total // 12, luni_total % 12


def este_major(data_nasterii):
    if data_nasterii > datetime.date.today():
        raise ValidationError("Data nasterii nu poate fi in viitor.", code="data_viitor")
    if varsta_ani_luni(data_nasterii)[0] < 18:
        raise ValidationError("Trebuie sa aveti cel putin 18 ani.", code="minor")


def data_din_cnp(cnp):
    """Returneaza data nasterii codificata in CNP sau None daca nu e valida."""
    secol = {"1": 1900, "2": 1900, "5": 2000, "6": 2000}.get(cnp[0])
    if secol is None:
        return None
    try:
        return datetime.date(secol + int(cnp[1:3]), int(cnp[3:5]), int(cnp[5:7]))
    except ValueError:
        return None


def valideaza_cnp(cnp):  # (0.2)
    if not cnp:
        return
    if not cnp.isdigit():
        raise ValidationError("CNP-ul trebuie sa contina doar cifre.", code="cnp_cifre")
    if cnp[0] not in "1256":
        raise ValidationError("CNP-ul trebuie sa inceapa cu 1, 2, 5 sau 6.", code="cnp_inceput")
    if data_din_cnp(cnp) is None:
        raise ValidationError("Cifrele 2-7 din CNP nu formeaza o data valida.", code="cnp_data")


DOMENII_TEMPORARE = ("guerillamail.com", "yopmail.com")


def email_netemporar(email):  # (0.1)
    domeniu = (email or "").rsplit("@", 1)[-1].lower()
    if any(domeniu == d or domeniu.endswith("." + d) for d in DOMENII_TEMPORARE):
        raise ValidationError("Nu se accepta adrese de e-mail temporare.", code="email_temporar")


def telefon_valid(telefon):
    if telefon and not re.fullmatch(r"(\+40|0)7\d{8}", telefon.replace(" ", "")):
        raise ValidationError("Telefonul trebuie sa fie de forma 07xxxxxxxx sau +407xxxxxxxx.", code="telefon")


# ----------------------------------------------------------------- cod cerere (contact)
# Algoritm: 3 litere mari + 5 cifre + 1 litera mica de control.
# Litera de control = chr(ord('a') + (suma codurilor ASCII ale primelor 8 caractere * 7) % 26)


def _litera_control(baza):
    return chr(ord("a") + (sum(map(ord, baza)) * 7) % 26)


def genereaza_cod_cerere():
    baza = "".join(random.choices(string.ascii_uppercase, k=3)) + "".join(random.choices(string.digits, k=5))
    return baza + _litera_control(baza)


def cod_cerere_valid(cod):
    return bool(cod and re.fullmatch(r"[A-Z]{3}\d{5}[a-z]", cod) and cod[-1] == _litera_control(cod[:-1]))


# ----------------------------------------------------------------- produse (ModelForm, Lab 5 Task 4)
# doua functii externe aplicate in ordine pe campul nume (fara_caractere_speciale e folosita si pe descriere)


def fara_caractere_speciale(valoare):
    if re.search(r"[<>{}$#@!]", valoare or ""):
        raise ValidationError("Nu sunt permise caracterele < > { } $ # @ !", code="caractere_speciale")


def nu_doar_majuscule(valoare):
    litere = [c for c in (valoare or "") if c.isalpha()]
    if len(litere) > 3 and all(c.isupper() for c in litere):
        raise ValidationError("Nu scrieti totul cu majuscule.", code="doar_majuscule")
