from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def qs(context, **modificari):
    """Query string-ul curent cu modificari. Valoarea None scoate parametrul. pagina se reseteaza implicit."""
    params = context["request"].GET.copy()
    if "pagina" not in modificari:
        params.pop("pagina", None)
    for cheie, valoare in modificari.items():
        params.pop(cheie, None)
        if valoare is not None:
            params[cheie] = valoare
    return "?" + params.urlencode() if params else "?"


@register.simple_tag(takes_context=True)
def qs_tag(context, tag, actiune="adauga"):
    """Adauga sau scoate un tag din filtrare, pastrand restul parametrilor."""
    params = context["request"].GET.copy()
    params.pop("pagina", None)
    taguri = [t for t in params.getlist("tag") if t != tag]
    if actiune == "adauga":
        taguri.append(tag)
    params.setlist("tag", taguri)
    return "?" + params.urlencode() if params else "?"


@register.filter
def get_item(dictionar, cheie):
    return dictionar.get(cheie)
