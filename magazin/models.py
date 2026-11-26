"""
Modelele proiectului.

  * Lab 2 Task 3 / Lab 3 Task 1: entitatile din diagrama (Categorie, Brand, Produs, IstoricPret,
    ServiciuAditional, ArticolBlog).
  * Lab 5 Task 3: Departament si TipMesaj (pentru pagina de contact).
  * Lab 6: Utilizator, Profil, Angajat, Comanda (+ ComandaProdus), Review, Favorit, Voucher.

Unde se gasesc cerintele din Lab 3 Task 1 (cauta in fisier dupa "[L3-..]"):
  [L3-null]        >= 5 campuri null=True
  [L3-unique]      >= 1 camp unic (altul decat id)
  [L3-email/url/slug]  EmailField, URLField, SlugField
  [L3-ordering]    ordonare implicita pentru >= 2 modele
  [L3-choices]     camp cu choices
  [L3-default]     >= 4 campuri cu default (unul blank=True in admin)
  [L3-help]        >= 5 help_text
  [L3-datetime]    DateTimeField cu data adaugarii ca valoare implicita
  [L3-errors]      >= 5 campuri cu error_messages
  [L3-Q]           >= 5 constrangeri cu models.Q
  [L3-index]       >= 4 indexuri
  [L3-image]       ImageField
"""
import datetime

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone


# =============================================================================
# Lab 2/3: entitatile din diagrama (firma si produsele)
# =============================================================================


class Categorie(models.Model):
    # Lab 2: categoria are obligatoriu nume, descriere, culoare, sigla (+ afisata_in_meniu ales de noi)
    nume = models.CharField(
        max_length=50,
        unique=True,  # [L3-unique]
        error_messages={  # [L3-errors] 1
            "unique": "Exista deja o categorie cu acest nume.",
            "max_length": "Numele categoriei poate avea maxim 50 de caractere.",
        },
    )
    # [L3-email/url/slug] SlugField; folosit in URL-ul /categorii/<slug>/ (Lab 4)
    slug = models.SlugField(
        max_length=60,
        unique=True,
        help_text="Partea din URL pentru pagina categoriei (de ex. placi-video).",  # [L3-help] 1
    )
    descriere = models.TextField(null=True, blank=True)  # [L3-null] 1
    culoare = models.CharField(
        max_length=7,
        default="#2b6cb0",  # [L3-default] 1
        help_text="Culoare reprezentativa in format hex (#rrggbb), folosita la stilizarea produselor.",  # [L3-help] 2
    )
    sigla = models.CharField(
        max_length=50,
        default="fa-solid fa-microchip",  # [L3-default] 2
        help_text="Clasa unui icon FontAwesome, de ex. fa-solid fa-memory.",  # [L3-help] 3
    )
    afisata_in_meniu = models.BooleanField(default=True)  # [L3-default] 3

    class Meta:
        verbose_name = "categorie"
        verbose_name_plural = "categorii"  # Lab 3 Task 2: pluralul corect in admin
        ordering = ["nume"]  # [L3-ordering] 1
        constraints = [
            # [L3-Q] 1: culoarea trebuie sa fie un cod hex valid
            models.CheckConstraint(
                condition=Q(culoare__regex=r"^#[0-9A-Fa-f]{6}$"),
                name="categorie_culoare_hex",
                violation_error_message="Culoarea trebuie sa fie de forma #rrggbb.",
            ),
        ]

    def __str__(self):  # Lab 3 Task 2: afisarea in admin
        return self.nume

    def get_absolute_url(self):
        return reverse("categorie", args=[self.slug])


class Brand(models.Model):
    nume = models.CharField(
        max_length=50,
        unique=True,
        error_messages={"unique": "Acest brand exista deja."},  # [L3-errors] 2
    )
    tara_origine = models.CharField(max_length=50)
    url_suport_drivere = models.URLField(  # [L3-email/url/slug] URLField
        null=True,  # [L3-null] 2
        blank=True,
        help_text="Pagina oficiala de unde clientii pot descarca drivere.",  # [L3-help] 4
        error_messages={"invalid": "Introduceti un URL valid (incepe cu http:// sau https://)."},  # [L3-errors] 3
    )

    class Meta:
        verbose_name = "brand"
        verbose_name_plural = "branduri"
        ordering = ["nume"]  # [L3-ordering] 2

    def __str__(self):
        return f"{self.nume} ({self.tara_origine})"


class ServiciuAditional(models.Model):
    nume = models.CharField(max_length=80, unique=True)
    tarif = models.DecimalField(max_digits=8, decimal_places=2)
    disponibil_online = models.BooleanField(default=True)

    class Meta:
        verbose_name = "serviciu aditional"
        verbose_name_plural = "servicii aditionale"
        constraints = [
            models.CheckConstraint(condition=Q(tarif__gte=0), name="serviciu_tarif_pozitiv"),  # [L3-Q] 2
        ]

    def __str__(self):
        return f"{self.nume} - {str(self.tarif).replace('.', ',')} lei"  # virgula zecimala, ca in restul site-ului


class Produs(models.Model):
    # [L3-choices] campul "stare" (enum in diagrama) admite doar aceste valori
    class Stare(models.TextChoices):
        NOU = "nou", "Nou"
        RESIGILAT = "resigilat", "Resigilat"
        PRECOMANDA = "precomanda", "Precomanda"
        RECONDITIONAT = "reconditionat", "Reconditionat"

    # --- atributele din diagrama (Lab 2: minim 7)
    nume = models.CharField(
        max_length=100,
        error_messages={  # [L3-errors] 4
            "max_length": "Numele produsului poate avea maxim 100 de caractere.",
            "blank": "Produsul trebuie sa aiba un nume.",
        },
    )
    pret_curent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        error_messages={"invalid": "Pretul trebuie sa fie un numar (de ex. 1299.99)."},  # [L3-errors] 5
    )
    stoc_online = models.PositiveIntegerField(
        default=0,  # [L3-default] 4
        help_text="Numarul de bucati disponibile pentru comanda online.",  # [L3-help] 5
    )
    consum_w = models.PositiveIntegerField(
        null=True,  # [L3-null] 3
        blank=True,
        help_text="Consumul maxim in wati (TDP pentru procesoare/placi video). Lasati gol pentru accesorii.",
    )
    stare = models.CharField(max_length=15, choices=Stare.choices, default=Stare.NOU)  # [L3-choices]
    data_lansare = models.DateField(null=True, blank=True)  # [L3-null] 4
    # Lab 2: atributul cu valori multiple (vector) din diagrama -> ArrayField (doar PostgreSQL)
    interfete_conectare = ArrayField(
        models.CharField(max_length=30),
        default=list,  # [L3-default] 5: blank=True -> poate ramane gol in formularul din admin
        blank=True,
        help_text="Interfete separate prin virgula, de ex. PCIe 4.0 x16,HDMI 2.1",
    )

    # --- campuri cerute de laboratoarele urmatoare
    slug = models.SlugField(max_length=120, unique=True)
    descriere = models.TextField(null=True, blank=True)  # [L3-null] 5
    taguri = ArrayField(models.CharField(max_length=30), default=list, blank=True)  # Lab 4: taguri ca ArrayField
    imagine = models.ImageField(upload_to="produse/", null=True, blank=True)  # [L3-image] [L3-null] 6
    data_adaugare = models.DateTimeField(default=timezone.now, editable=False)  # [L3-datetime]

    # --- relatiile din diagrama
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT, related_name="produse")  # 1-N "Clasifica"
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="produse")  # 1-N "Produce"
    servicii = models.ManyToManyField(ServiciuAditional, blank=True, related_name="produse")  # M-N "Permite"

    class Meta:
        verbose_name = "produs"
        verbose_name_plural = "produse"
        ordering = ["nume"]  # [L3-ordering] 3
        indexes = [
            models.Index(fields=["nume"], name="produs_nume_idx"),  # [L3-index] 1: cautare dupa nume
            models.Index(fields=["pret_curent"], name="produs_pret_idx"),  # [L3-index] 2: filtrare/sortare pret
            models.Index(fields=["categorie", "stare"], name="produs_categ_stare_idx"),  # [L3-index] 3
            models.Index(fields=["-data_lansare"], name="produs_lansare_idx"),  # [L3-index] 4: "noutati"
            GinIndex(fields=["taguri"], name="produs_taguri_gin"),  # [L3-index] 5: filtrare dupa taguri
        ]
        constraints = [
            models.CheckConstraint(  # [L3-Q] 3
                condition=Q(pret_curent__gt=0),
                name="produs_pret_pozitiv",
                violation_error_message="Pretul trebuie sa fie mai mare ca 0.",
            ),
            models.CheckConstraint(  # [L3-Q] 4
                condition=Q(consum_w__isnull=True) | Q(consum_w__lte=3000),
                name="produs_consum_realist",
                violation_error_message="Consumul nu poate depasi 3000 W.",
            ),
            models.CheckConstraint(  # [L3-Q] 5: precomanda => stoc 0
                condition=~Q(stare="precomanda") | Q(stoc_online=0),
                name="produs_precomanda_fara_stoc",
                violation_error_message="Un produs in precomanda nu poate avea stoc.",
            ),
            models.CheckConstraint(  # [L3-Q] 6
                condition=Q(data_lansare__isnull=True) | Q(data_lansare__gte=datetime.date(1990, 1, 1)),
                name="produs_lansare_dupa_1990",
            ),
        ]

    def __str__(self):
        return self.nume

    def get_absolute_url(self):
        # Lab 4: pagina proprie a produsului
        return reverse("produs", args=[self.id])

    @property
    def stoc_limitat(self):
        # Lab 4: STOC_MIN din settings.py
        return self.stoc_online < settings.STOC_MIN


class IstoricPret(models.Model):
    """Entitatea SLABA din diagrama: exista doar impreuna cu produsul ei.
    Cheia ei e (produs, nr_modificare); nr_modificare singur nu identifica un rand."""

    produs = models.ForeignKey(Produs, on_delete=models.CASCADE, related_name="istoric_preturi")
    nr_modificare = models.PositiveIntegerField()  # cheie partiala (subliniata punctat in diagrama)
    valoare_pret = models.DecimalField(max_digits=10, decimal_places=2)
    data_aplicare = models.DateField(default=datetime.date.today)

    class Meta:
        verbose_name = "istoric pret"
        verbose_name_plural = "istoric preturi"
        ordering = ["produs", "-nr_modificare"]
        constraints = [
            models.UniqueConstraint(fields=["produs", "nr_modificare"], name="istoric_cheie_partiala"),
            models.CheckConstraint(condition=Q(valoare_pret__gt=0), name="istoric_pret_pozitiv"),  # [L3-Q] 7
        ]

    def __str__(self):
        return f"{self.produs} #{self.nr_modificare}: {str(self.valoare_pret).replace('.', ',')} lei"


class ArticolBlog(models.Model):
    titlu = models.CharField(
        max_length=150,
        error_messages={"max_length": "Titlul poate avea maxim 150 de caractere."},
    )
    continut = models.TextField()
    data_publicarii = models.DateField(default=datetime.date.today)
    produse = models.ManyToManyField(Produs, blank=True, related_name="articole")  # M-N "Prezentat_In"

    class Meta:
        verbose_name = "articol blog"
        verbose_name_plural = "articole blog"
        ordering = ["-data_publicarii"]

    def __str__(self):
        return self.titlu


# =============================================================================
# Lab 5 Task 3: departamente si tipuri de mesaje (pagina de contact).
# Tabelul de legatura TipMesaj <-> Departament e creat automat de ManyToManyField.
# =============================================================================


class Departament(models.Model):
    nume = models.CharField(max_length=60, unique=True)
    email = models.EmailField(null=True, blank=True)  # [L3-email/url/slug] EmailField
    # Lab 6: seful departamentului e un angajat (poate fi null)
    sef = models.ForeignKey(
        "Angajat", on_delete=models.SET_NULL, null=True, blank=True, related_name="departamente_conduse"
    )

    class Meta:
        verbose_name = "departament"
        verbose_name_plural = "departamente"
        ordering = ["nume"]

    def __str__(self):
        return self.nume


class TipMesaj(models.Model):
    cod = models.SlugField(max_length=20, unique=True)  # reclamatie, intrebare, review, cerere, programare
    nume = models.CharField(max_length=40)
    # minimul de zile de asteptare, folosit la validarea formularului de contact
    min_zile = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        help_text="Minimul de zile de asteptare pentru acest tip de mesaj.",
    )
    departamente = models.ManyToManyField(Departament, related_name="tipuri_mesaje")

    class Meta:
        verbose_name = "tip mesaj"
        verbose_name_plural = "tipuri mesaje"
        ordering = ["nume"]

    def __str__(self):
        return self.nume


# =============================================================================
# Lab 6: utilizatori si entitatile legate de ei
# =============================================================================


class Utilizator(AbstractUser):
    """Utilizatorul personalizat (AUTH_USER_MODEL in settings.py).
    AbstractUser aduce deja: username, first_name (prenume), last_name (nume), email, password.
    Atribute suplimentare (Lab 6: minim 5, dintre care minim 2 optionale in Profil):
    aici telefon, data_nasterii, oras; in Profil judet, strada, cod_postal, newsletter."""

    telefon = models.CharField(max_length=15, null=True, blank=True)
    data_nasterii = models.DateField(null=True, blank=True)
    oras = models.CharField(max_length=50, null=True, blank=True)
    # null=True doar ca sa mearga "createsuperuser"; in formularul de inregistrare sunt obligatorii

    class Meta:
        verbose_name = "utilizator"
        verbose_name_plural = "utilizatori"

    def __str__(self):
        return self.username


class Profil(models.Model):
    """Lab 6: date optionale, legate one-to-one de utilizator.
    Se creeaza doar daca utilizatorul completeaza macar un camp (vezi views.register_view)."""

    utilizator = models.OneToOneField(Utilizator, on_delete=models.CASCADE, related_name="profil")
    judet = models.CharField(max_length=40, null=True, blank=True)
    strada = models.CharField(max_length=120, null=True, blank=True)
    cod_postal = models.CharField(max_length=6, null=True, blank=True)
    newsletter = models.BooleanField(default=False)

    class Meta:
        verbose_name = "profil"
        verbose_name_plural = "profiluri"

    def __str__(self):
        return f"Profil {self.utilizator}"


class Angajat(models.Model):
    """Lab 6: one-to-one cu Utilizator, legat de Departament; doar datele de angajat."""

    utilizator = models.OneToOneField(Utilizator, on_delete=models.CASCADE, related_name="angajat")
    departament = models.ForeignKey(Departament, on_delete=models.PROTECT, related_name="angajati")
    functie = models.CharField(max_length=60)
    data_angajare = models.DateField(default=datetime.date.today)
    salariu = models.DecimalField(max_digits=9, decimal_places=2)

    class Meta:
        verbose_name = "angajat"
        verbose_name_plural = "angajati"

    def __str__(self):
        return f"{self.utilizator.get_full_name() or self.utilizator} - {self.functie}"


class Comanda(models.Model):
    """Lab 6: minim 3 atribute in afara de id, produse si utilizator
    (data_plasarii, status, prin_curier, adresa_livrare)."""

    class Status(models.TextChoices):
        PLASATA = "plasata", "Plasata"
        PROCESARE = "procesare", "In procesare"
        EXPEDIATA = "expediata", "Expediata"
        LIVRATA = "livrata", "Livrata"
        ANULATA = "anulata", "Anulata"

    utilizator = models.ForeignKey(Utilizator, on_delete=models.PROTECT, related_name="comenzi")
    data_plasarii = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PLASATA)
    prin_curier = models.BooleanField(default=True)
    adresa_livrare = models.CharField(max_length=200)
    # Many-to-Many cu Produs PRIN tabelul ComandaProdus, care retine si cantitatea
    produse = models.ManyToManyField(Produs, through="ComandaProdus", related_name="comenzi")

    class Meta:
        verbose_name = "comanda"
        verbose_name_plural = "comenzi"
        ordering = ["-data_plasarii"]

    def __str__(self):
        return f"Comanda #{self.id} ({self.utilizator})"


class ComandaProdus(models.Model):
    """Lab 6: tabelul de legatura comanda-produs, cu numarul de bucati."""

    comanda = models.ForeignKey(Comanda, on_delete=models.CASCADE)
    produs = models.ForeignKey(Produs, on_delete=models.PROTECT)
    cantitate = models.PositiveIntegerField(default=1)
    pret_unitar = models.DecimalField(max_digits=10, decimal_places=2)  # pretul din momentul comenzii

    class Meta:
        verbose_name = "produs din comanda"
        verbose_name_plural = "produse din comenzi"
        constraints = [
            models.UniqueConstraint(fields=["comanda", "produs"], name="comanda_produs_unic"),
            models.CheckConstraint(condition=Q(cantitate__gte=1), name="comanda_cantitate_minim_1"),
        ]


# --- Lab 6: cele 3 entitati suplimentare legate de utilizator (Review, Favorit, Voucher)


class Review(models.Model):
    utilizator = models.ForeignKey(Utilizator, on_delete=models.CASCADE, related_name="reviewuri")
    produs = models.ForeignKey(Produs, on_delete=models.CASCADE, related_name="reviewuri")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField(blank=True)
    data = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "review"
        verbose_name_plural = "reviewuri"
        constraints = [
            models.UniqueConstraint(fields=["utilizator", "produs"], name="un_review_per_produs"),
            models.CheckConstraint(condition=Q(rating__gte=1) & Q(rating__lte=5), name="review_rating_1_5"),
        ]


class Favorit(models.Model):
    utilizator = models.ForeignKey(Utilizator, on_delete=models.CASCADE, related_name="favorite")
    produs = models.ForeignKey(Produs, on_delete=models.CASCADE, related_name="favorit_la")
    data_adaugarii = models.DateTimeField(default=timezone.now)
    notificare_reducere = models.BooleanField(default=False)

    class Meta:
        verbose_name = "produs favorit"
        verbose_name_plural = "produse favorite"
        constraints = [
            models.UniqueConstraint(fields=["utilizator", "produs"], name="favorit_unic"),
        ]


class Voucher(models.Model):
    cod = models.CharField(max_length=20, unique=True)
    procent_reducere = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(90)]
    )
    data_expirare = models.DateTimeField()
    utilizator = models.ForeignKey(
        Utilizator, on_delete=models.CASCADE, null=True, blank=True, related_name="vouchere"
    )
    folosit = models.BooleanField(default=False)

    class Meta:
        verbose_name = "voucher"
        verbose_name_plural = "vouchere"

    def __str__(self):
        return self.cod
