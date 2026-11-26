"""Semnale ale aplicatiei.

Django creeaza automat permisiunile cu nume in engleza ("Can add produs"), iar ele apar in admin
la Utilizatori si Grupuri. Dupa fiecare `migrate` le redenumim in romana ("Poate adauga produs").
"""
from django.conf import settings
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import translation

ACTIUNI_RO = {
    "add": "Poate adăuga",
    "change": "Poate modifica",
    "delete": "Poate șterge",
    "view": "Poate vizualiza",
}


@receiver(post_migrate)
def permisiuni_in_romana(sender, using="default", **kwargs):
    from django.contrib.auth.models import Permission

    # migrate ruleaza fara limba activa, asa ca activam romana ca "group" sa devina "grup"
    with translation.override(settings.LANGUAGE_CODE):
        _redenumeste(Permission, using)


def _redenumeste(Permission, using):
    for perm in Permission.objects.using(using).select_related("content_type"):
        actiune = perm.codename.split("_", 1)[0]
        model = perm.content_type.model_class()
        if actiune not in ACTIUNI_RO or model is None or perm.codename != f"{actiune}_{model._meta.model_name}":
            continue  # permisiunile proprii (adaugate in Meta.permissions) raman cum sunt
        nume = f"{ACTIUNI_RO[actiune]} {model._meta.verbose_name}"[:255]
        if perm.name != nume:
            perm.name = nume
            perm.save(update_fields=["name"])
