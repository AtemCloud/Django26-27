"""Lab 1/2: middleware care afla IP-ul utilizatorului si creeaza un obiect Accesare la fiecare cerere.
Este activat in settings.py, in lista MIDDLEWARE."""
from .views import ACCESARI, PREFIX_APLICATIE, Accesare


def get_ip(request):
    # functia din laboratorul 1 pentru obtinerea ip-ului unei cereri
    req_headers = request.META
    str_lista_ip = request.META.get('HTTP_X_FORWARDED_FOR')
    if str_lista_ip:
        return str_lista_ip.split(',')[-1].strip()
    else:
        return request.META.get('REMOTE_ADDR')


class AccesareMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # IP-ul e afisat in footer-ul tuturor paginilor (baza.html: request.ip_client)
        request.ip_client = get_ip(request)
        # doar cererile catre paginile magazinului (nu admin, fisiere statice sau /api/)
        if request.path.startswith(PREFIX_APLICATIE) and not request.path.startswith(PREFIX_APLICATIE + "/api/"):
            parametri = {}
            for nume in request.GET:
                valori = request.GET.getlist(nume)
                parametri[nume] = valori[0] if len(valori) == 1 else valori
            acces = Accesare(request.ip_client, request.path, parametri)
            ACCESARI.append(acces)
            request.acces = acces  # folosit de views.info
            print(acces)  # stringul accesarii (metoda __str__) in consola
        response = self.get_response(request)
        return response
