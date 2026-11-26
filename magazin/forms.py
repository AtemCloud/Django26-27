import datetime
from decimal import Decimal

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from django.utils.text import slugify

from . import validators as v
from .models import Brand, Categorie, Departament, Produs, Profil, ServiciuAditional, TipMesaj, Utilizator

# =============================================================================
# Lab 5 Task 2: filtrarea produselor
# =============================================================================

COLOANE_SORTARE = {
    "nume": "Nume",
    "pret_curent": "Pret",
    "stoc_online": "Stoc",
    "data_lansare": "Data lansarii",
    "consum_w": "Consum",
}


class FiltruProduseForm(forms.Form):
    """Lab 5 Task 2: filtre pentru toate campurile produsului (forms.Form).
    Folosit si pe pagina tuturor produselor si pe paginile categoriilor (views.afisare_produse).
    Widget-ul corespunde tipului: DateInput type=date, select pentru choices/FK, number pentru numere."""

    PE_PAGINA = [(6, "6"), (12, "12"), (18, "18"), (24, "24")]  # divizibile cu 1, 2 si 3
    COLOANE = [(1, "1 coloana"), (2, "2 coloane"), (3, "3 coloane")]

    nume = forms.CharField(required=False, max_length=100, label="Nume contine")
    descriere = forms.CharField(required=False, max_length=100, label="Descriere contine")
    # pret: doua inputuri, minim si maxim
    pret_min = forms.DecimalField(required=False, min_value=0, label="Pret minim",
                                  error_messages={"min_value": "Pretul minim nu poate fi negativ."})
    pret_max = forms.DecimalField(required=False, min_value=0, label="Pret maxim",
                                  error_messages={"min_value": "Pretul maxim nu poate fi negativ."})
    stoc_min = forms.IntegerField(required=False, min_value=0, label="Stoc minim")
    consum_max = forms.IntegerField(required=False, min_value=0, label="Consum maxim (W)")
    stare = forms.ChoiceField(required=False, choices=[("", "oricare")] + Produs.Stare.choices)
    lansat_dupa = forms.DateField(required=False, label="Lansat dupa",
                                  widget=forms.DateInput(attrs={"type": "date"}))
    lansat_inainte = forms.DateField(required=False, label="Lansat inainte de",
                                     widget=forms.DateInput(attrs={"type": "date"}))
    interfata = forms.CharField(required=False, max_length=30, label="Interfata (de ex. AM5, HDMI)")
    categorie = forms.ModelChoiceField(required=False, queryset=Categorie.objects.all(), empty_label="toate")
    # filtrul care implica un ForeignKey (brandul producator)
    brand = forms.ModelChoiceField(required=False, queryset=Brand.objects.all(), empty_label="toate")
    serviciu = forms.ModelChoiceField(required=False, queryset=ServiciuAditional.objects.all(),
                                      empty_label="oricare", label="Ofera serviciul")
    # cate produse pe pagina (la schimbare -> mesaj despre repaginare) si pe cate coloane
    pe_pagina = forms.TypedChoiceField(choices=PE_PAGINA, coerce=int, required=False, label="Produse pe pagina")
    coloane = forms.TypedChoiceField(choices=COLOANE, coerce=int, required=False, label="Coloane")

    def __init__(self, *args, categorie_fixa=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.categorie_fixa = categorie_fixa
        self.fields["pe_pagina"].initial = 6
        self.fields["coloane"].initial = 3
        if categorie_fixa:
            # pe pagina categoriei: campul e ascuns si readonly, setat la categoria curenta.
            # Verificarea la server (daca a fost modificat din developer tools) e in views.afisare_produse
            self.fields["categorie"].widget = forms.HiddenInput(attrs={"readonly": "readonly"})
            self.fields["categorie"].initial = categorie_fixa.pk

    # ---- cele (minim) 3 validari cu mesaje personalizate
    def clean_nume(self):  # validarea 1
        nume = self.cleaned_data["nume"]
        v.fara_caractere_speciale(nume)
        return nume

    def clean_consum_max(self):  # validarea 2
        consum = self.cleaned_data["consum_max"]
        if consum is not None and consum > 3000:
            raise forms.ValidationError("Niciun produs nu consuma peste 3000 W.")
        return consum

    def clean(self):
        cleaned_data = super().clean()
        pret_min = cleaned_data.get("pret_min")  # validarea 3
        pret_max = cleaned_data.get("pret_max")
        if pret_min is not None and pret_max is not None and pret_min > pret_max:
            self.add_error("pret_max", "Pretul maxim trebuie sa fie mai mare decat pretul minim.")
        lansat_dupa = cleaned_data.get("lansat_dupa")  # validarea 4
        lansat_inainte = cleaned_data.get("lansat_inainte")
        if lansat_dupa and lansat_inainte and lansat_dupa > lansat_inainte:
            self.add_error("lansat_inainte", "Intervalul de date e inversat.")
        return cleaned_data


# =============================================================================
# Lab 5 Task 3: formularul de contact
# =============================================================================

NESELECTAT = "neselectat"


class ContactForm(forms.Form):
    """Lab 5 Task 3. Fiecare camp e un rand din cerinta; validarile sunt marcate cu (0.x)."""

    # (0.1) nume + prenume; validatorii externi din validators.py: incepe_cu_majuscula (0.2)
    # si majuscula_dupa_separator (0.1), dati prin parametrul validators (fara cod repetat)
    nume = forms.CharField(
        max_length=10, validators=[v.incepe_cu_majuscula, v.majuscula_dupa_separator],
        error_messages={"required": "Numele este obligatoriu.",
                        "max_length": "Numele poate avea maxim 10 caractere."})
    prenume = forms.CharField(
        max_length=30, required=False, validators=[v.incepe_cu_majuscula, v.majuscula_dupa_separator],
        help_text="Mai multe prenume se separa prin spatiu sau cratima.",
        error_messages={"max_length": "Prenumele poate avea maxim 30 de caractere."})
    # (0.2) CNP optional, exact 13 caractere; contorul de cifre e in js/contact.js
    cnp = forms.CharField(
        label="CNP", min_length=13, max_length=13, required=False,
        widget=forms.TextInput(attrs={"data-contor": "13", "inputmode": "numeric"}),
        error_messages={"min_length": "CNP-ul are exact 13 cifre.", "max_length": "CNP-ul are exact 13 cifre."})
    # (0.1) data nasterii cu widget calendar
    data_nasterii = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        error_messages={"required": "Data nasterii este obligatorie.", "invalid": "Data nu e valida."})
    email = forms.EmailField(label="E-mail", error_messages={"required": "E-mailul este obligatoriu.",
                                                             "invalid": "Adresa de e-mail nu e valida."})
    confirmare_email = forms.EmailField(label="Confirmare e-mail",
                                        error_messages={"required": "Confirmati adresa de e-mail."})
    telefon = forms.CharField(required=False, max_length=15, help_text="Format: 07xxxxxxxx sau +407xxxxxxxx.")
    # (0.1) tip mesaj si (0.3) departament: optiunile vin din baza de date (TipMesaj, Departament);
    # lista de departamente se actualizeaza dinamic in browser (js/contact.js + /api/departamente/)
    tip_mesaj = forms.ChoiceField(label="Tip mesaj")
    departament = forms.ChoiceField(label="Departament destinatie")
    subiect = forms.CharField(
        max_length=100, validators=[v.incepe_cu_majuscula, v.fara_linkuri],
        error_messages={"required": "Subiectul este obligatoriu.",
                        "max_length": "Subiectul poate avea maxim 100 de caractere."})
    # (0.05) eticheta cu textul cerut e pusa ca help_text
    minim_zile_asteptare = forms.IntegerField(
        min_value=1, max_value=30, label="Minim zile asteptare",
        help_text=("Pentru review-uri/cereri minimul de zile de asteptare trebuie setat de la 4 incolo "
                   "iar pentru cereri/intrebari de la 2 incolo. Maximul e 30."),
        error_messages={"min_value": "Minimul e o zi.", "max_value": "Maximul e 30 de zile.",
                        "required": "Spuneti-ne cate zile puteti astepta."})
    mesaj = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 6}),
        label="Mesaj (va rugam sa va semnati la final cu numele)",  # semnatura ceruta prin label
        validators=[v.fara_linkuri], error_messages={"required": "Mesajul nu poate fi gol."})
    # (0.35) 3 imagini optionale; apar pe rand (js/contact.js)
    imagine1 = forms.ImageField(required=False, label="Imagine 1")
    imagine2 = forms.ImageField(required=False, label="Imagine 2")
    imagine3 = forms.ImageField(required=False, label="Imagine 3")
    # (0.2) GDPR obligatoriu; butonul de submit e blocat pana se bifeaza (js/contact.js)
    gdpr = forms.BooleanField(label="Sunt de acord cu prelucrarea datelor personale (GDPR)",
                              error_messages={"required": "Trebuie sa va dati acordul pentru prelucrarea datelor."})
    # (0.2) camp ascuns cu un cod generat de algoritmul nostru (validators.genereaza_cod_cerere)
    cod_cerere = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tipuri = {t.cod: t for t in TipMesaj.objects.prefetch_related("departamente")}
        self.fields["tip_mesaj"].choices = [(NESELECTAT, "neselectat")] + [(c, t.nume) for c, t in self.tipuri.items()]
        self.fields["tip_mesaj"].initial = NESELECTAT
        self.fields["departament"].choices = [(NESELECTAT, "neselectat")] + [
            (str(d.id), d.nume) for d in Departament.objects.all()]
        self.fields["departament"].initial = NESELECTAT
        if not self.is_bound:
            self.fields["cod_cerere"].initial = v.genereaza_cod_cerere()

    # ---------------------------------------------------- validari pe campuri
    def clean_data_nasterii(self):  # (0.1) expeditorul e major
        data = self.cleaned_data["data_nasterii"]
        v.este_major(data)
        return data

    def clean_mesaj(self):  # (0.3) 5-100 cuvinte, max 15 caractere/cuvant (+ fara linkuri, prin validators)
        mesaj = self.cleaned_data["mesaj"]
        lista = v.cuvinte(mesaj)
        if not 5 <= len(lista) <= 100:
            raise forms.ValidationError(f"Mesajul trebuie sa aiba intre 5 si 100 de cuvinte (are {len(lista)}).")
        lungi = [c for c in lista if len(c) > 15]
        if lungi:
            raise forms.ValidationError(f"Cuvintele pot avea maxim 15 caractere: {lungi[0]}")
        return mesaj

    def clean_tip_mesaj(self):  # (0.2) nu "neselectat" si doar valori din tabel
        tip = self.cleaned_data["tip_mesaj"]
        if tip == NESELECTAT:
            raise forms.ValidationError("Alegeti tipul mesajului.")
        if tip not in self.tipuri:
            raise forms.ValidationError("Tip de mesaj necunoscut.")
        return tip

    def clean_departament(self):
        dep = self.cleaned_data["departament"]
        if dep == NESELECTAT:
            raise forms.ValidationError("Alegeti departamentul.")
        try:
            return Departament.objects.get(pk=int(dep))
        except (ValueError, Departament.DoesNotExist):
            raise forms.ValidationError("Departament necunoscut.")

    def clean_cnp(self):  # (0.2) doar cifre, incepe cu 1/2/5/6, cifrele 2-7 sunt o data valida
        cnp = self.cleaned_data["cnp"]
        v.valideaza_cnp(cnp)
        return cnp

    def clean_email(self):  # (0.1) fara guerillamail.com / yopmail.com
        email = self.cleaned_data["email"]
        v.email_netemporar(email)
        return email

    def clean_telefon(self):
        telefon = self.cleaned_data["telefon"]
        v.telefon_valid(telefon)
        return telefon

    def clean_gdpr(self):  # (0.1) verificam din nou acordul (submit-ul putea fi deblocat manual)
        if not self.cleaned_data.get("gdpr"):
            raise forms.ValidationError("Fara acordul GDPR nu putem procesa mesajul.")
        return True

    def clean_cod_cerere(self):  # (0.2) codul putea fi generat de algoritmul nostru?
        cod = self.cleaned_data["cod_cerere"]
        if not v.cod_cerere_valid(cod):
            raise forms.ValidationError("Cererea nu este valida (cod de cerere incorect). Reincarcati pagina.")
        return cod

    # ---------------------------------------------------- validari generale
    def clean(self):
        cleaned_data = super().clean()
        # (0.1) validarea de la curs: e-mailul si confirmarea coincid
        email = cleaned_data.get("email")
        confirmare_email = cleaned_data.get("confirmare_email")
        if email and confirmare_email and email != confirmare_email:
            self.add_error("confirmare_email", "Adresele de e-mail nu coincid.")

        # (0.1) ultimul cuvant din mesaj e numele (semnatura)
        nume = cleaned_data.get("nume")
        mesaj = cleaned_data.get("mesaj")
        if nume and mesaj:
            lista = v.cuvinte(mesaj)
            if not lista or lista[-1] != nume:
                self.add_error("mesaj", f"Semnati-va: ultimul cuvant din mesaj trebuie sa fie numele ({nume}).")

        # (0.4) zilele de asteptare respecta minimul tipului de mesaj, citit din tabelul TipMesaj
        tip = self.tipuri.get(cleaned_data.get("tip_mesaj"))
        zile = cleaned_data.get("minim_zile_asteptare")
        if tip and zile is not None and zile < tip.min_zile:
            self.add_error("minim_zile_asteptare",
                           f"Pentru {tip.nume.lower()} minimul de zile de asteptare este {tip.min_zile}.")

        # (0.1) CNP-ul corespunde cu data nasterii
        cnp = cleaned_data.get("cnp")
        data_nasterii = cleaned_data.get("data_nasterii")
        if cnp and data_nasterii and v.data_din_cnp(cnp) != data_nasterii:
            self.add_error("cnp", "CNP-ul nu corespunde cu data nasterii.")

        # (0.3) anti-manipulare: departamentul chiar primeste acest tip de mesaj (tabelul de legatura)
        departament = cleaned_data.get("departament")
        if tip and departament and departament not in tip.departamente.all():
            self.add_error("departament", f"Departamentul {departament} nu primeste mesaje de tip {tip.nume.lower()}.")
        return cleaned_data


# =============================================================================
# Lab 5 Task 4: adaugare produse (ModelForm)
# =============================================================================


class ProdusForm(forms.ModelForm):
    """Lab 5 Task 4. Inputuri pentru coloane: cele din Meta.fields.
    Inputuri aditionale: pret_achizitie + adaos_procent -> coloana pret_curent,
    taguri_text -> taguri, interfete_text -> interfete_conectare.
    Coloanele lipsa se calculeaza in views.adauga_produs, dupa form.save(commit=False)."""

    # inputuri aditionale (nu exista ca si coloane)
    pret_achizitie = forms.DecimalField(
        min_value=Decimal("0.01"), decimal_places=2, label="Pret de achizitie (lei)",
        help_text="Pretul platit furnizorului.",
        error_messages={"min_value": "Pretul de achizitie trebuie sa fie pozitiv.",
                        "required": "Introduceti pretul de achizitie."})
    adaos_procent = forms.IntegerField(
        min_value=0, max_value=200, initial=25, label="Adaos comercial (%)",
        help_text="Pretul de vanzare = pret achizitie + adaos.",
        error_messages={"min_value": "Adaosul nu poate fi negativ.", "max_value": "Adaosul maxim e 200%%.",
                        "required": "Introduceti adaosul."})
    taguri_text = forms.CharField(
        required=False, label="Taguri", help_text="Separate prin virgula, de ex. gaming, rgb, ddr5")
    interfete_text = forms.CharField(required=False, label="Interfete de conectare",
                                     help_text="Separate prin virgula, de ex. PCIe 4.0 x16, HDMI 2.1")

    class Meta:
        model = Produs
        fields = ["nume", "descriere", "categorie", "brand", "stare", "stoc_online", "consum_w",
                  "data_lansare", "imagine", "servicii"]
        # etichete personalizate (minim 2)
        labels = {"nume": "Denumire produs", "stoc_online": "Bucati in stoc", "consum_w": "Consum (W)"}
        widgets = {"data_lansare": forms.DateInput(attrs={"type": "date"}),
                   "servicii": forms.CheckboxSelectMultiple}
        # toate mesajele de eroare sunt personalizate
        error_messages = {
            "nume": {"required": "Produsul trebuie sa aiba o denumire.", "max_length": "Maxim 100 de caractere."},
            "categorie": {"required": "Alegeti categoria."},
            "brand": {"required": "Alegeti brandul."},
            "stoc_online": {"invalid": "Stocul e un numar intreg.", "min_value": "Stocul nu poate fi negativ."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # validare cu doua functii externe, aplicate in ordine prin "validators":
        # fara_caractere_speciale e folosita si pentru campul descriere
        self.fields["nume"].validators += [v.fara_caractere_speciale, v.nu_doar_majuscule]
        self.fields["descriere"].validators += [v.fara_caractere_speciale]

    # ---- minim 3 validari proprii pe campuri
    def clean_nume(self):
        nume = self.cleaned_data["nume"].strip()
        if len(nume) < 3:
            raise forms.ValidationError("Denumirea trebuie sa aiba minim 3 caractere.")
        if Produs.objects.filter(slug=slugify(nume)).exists():
            raise forms.ValidationError("Exista deja un produs cu aceasta denumire.")
        return nume

    def clean_data_lansare(self):
        data = self.cleaned_data["data_lansare"]
        if data and data > datetime.date.today() + datetime.timedelta(days=365):
            raise forms.ValidationError("Data lansarii nu poate fi la mai mult de un an in viitor.")
        return data

    def clean_taguri_text(self):
        taguri = [t.strip().lower() for t in self.cleaned_data["taguri_text"].split(",") if t.strip()]
        if len(taguri) > 8:
            raise forms.ValidationError("Maxim 8 taguri.")
        if any(len(t) > 30 for t in taguri):
            raise forms.ValidationError("Un tag poate avea maxim 30 de caractere.")
        return taguri

    def clean_interfete_text(self):
        return [i.strip() for i in self.cleaned_data["interfete_text"].split(",") if i.strip()]

    def clean(self):
        cleaned_data = super().clean()
        # validare la nivelul formularului (mai multe campuri): stare + stoc_online
        if cleaned_data.get("stare") == Produs.Stare.PRECOMANDA and cleaned_data.get("stoc_online"):
            self.add_error("stoc_online", "Produsele in precomanda trebuie sa aiba stocul 0.")
        # a doua validare pe mai multe campuri: pret_achizitie + adaos_procent
        pret_achizitie = cleaned_data.get("pret_achizitie")
        adaos_procent = cleaned_data.get("adaos_procent")
        if pret_achizitie is not None and adaos_procent is not None and pret_achizitie * (100 + adaos_procent) / 100 > 100000:
            self.add_error("adaos_procent", "Pretul final ar depasi 100.000 lei.")
        return cleaned_data


# =============================================================================
# Lab 6: utilizatori
# =============================================================================


class CustomUserCreationForm(UserCreationForm):
    """Lab 6: toate campurile utilizatorului + campurile din Profil (optionale).
    Validari pe campurile suplimentare: telefon, data_nasterii, oras (+ cod_postal, email)."""

    judet = forms.CharField(required=False, max_length=40)
    strada = forms.CharField(required=False, max_length=120)
    cod_postal = forms.CharField(required=False, max_length=6, label="Cod postal")
    newsletter = forms.BooleanField(required=False, label="Vreau sa primesc oferte pe e-mail")

    CAMPURI_PROFIL = ["judet", "strada", "cod_postal", "newsletter"]

    class Meta(UserCreationForm.Meta):
        model = Utilizator
        fields = ["username", "first_name", "last_name", "email", "telefon", "data_nasterii", "oras"]
        labels = {"first_name": "Prenume", "last_name": "Nume", "oras": "Oras"}
        widgets = {"data_nasterii": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for camp in ["first_name", "last_name", "email", "telefon", "data_nasterii", "oras"]:
            self.fields[camp].required = True
        self.fields["telefon"].help_text = "Format: 07xxxxxxxx"

    def clean_email(self):
        email = self.cleaned_data["email"]
        v.email_netemporar(email)
        if Utilizator.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Exista deja un cont cu acest e-mail.")
        return email

    def clean_telefon(self):
        telefon = self.cleaned_data["telefon"]
        v.telefon_valid(telefon)
        return telefon

    def clean_data_nasterii(self):
        data = self.cleaned_data["data_nasterii"]
        if data > datetime.date.today():
            raise forms.ValidationError("Data nasterii nu poate fi in viitor.")
        if v.varsta_ani_luni(data)[0] < 14:
            raise forms.ValidationError("Trebuie sa aveti minim 14 ani pentru a crea un cont.")
        return data

    def clean_oras(self):
        oras = self.cleaned_data["oras"]
        v.incepe_cu_majuscula(oras)
        return oras

    def clean_cod_postal(self):
        cod = self.cleaned_data["cod_postal"]
        if cod and not (cod.isdigit() and len(cod) == 6):
            raise forms.ValidationError("Codul postal are 6 cifre.")
        return cod

    def date_profil(self):
        return {c: self.cleaned_data.get(c) for c in self.CAMPURI_PROFIL}

    def profil_completat(self):
        return any(self.cleaned_data.get(c) for c in self.CAMPURI_PROFIL)


class CustomAuthenticationForm(AuthenticationForm):
    """Lab 6: login personalizat cu checkbox pentru a ramane logat o zi (folosit in views.custom_login_view)."""

    ramane_logat = forms.BooleanField(
        required=False,
        initial=False,
        label="Ramaneti logat (o zi)"
    )

    error_messages = {
        "invalid_login": "Numele de utilizator sau parola sunt gresite.",
        "inactive": "Contul este inactiv.",
    }

    def clean(self):
        cleaned_data = super().clean()
        ramane_logat = self.cleaned_data.get("ramane_logat")
        return cleaned_data


class EditareContForm(forms.ModelForm):
    class Meta:
        model = Utilizator
        fields = ["first_name", "last_name", "email", "telefon", "data_nasterii", "oras"]
        labels = {"first_name": "Prenume", "last_name": "Nume"}
        widgets = {"data_nasterii": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def clean_telefon(self):
        telefon = self.cleaned_data["telefon"]
        v.telefon_valid(telefon)
        return telefon


class EditareProfilForm(forms.ModelForm):
    class Meta:
        model = Profil
        fields = ["judet", "strada", "cod_postal", "newsletter"]
        labels = {"cod_postal": "Cod postal", "newsletter": "Vreau sa primesc oferte pe e-mail"}

    def clean_cod_postal(self):
        cod = self.cleaned_data["cod_postal"]
        if cod and not (cod.isdigit() and len(cod) == 6):
            raise forms.ValidationError("Codul postal are 6 cifre.")
        return cod


class CustomPasswordChangeForm(PasswordChangeForm):
    error_messages = {
        **PasswordChangeForm.error_messages,
        "password_incorrect": "Parola veche nu este corecta.",
        "password_mismatch": "Cele doua parole noi nu coincid.",
    }
