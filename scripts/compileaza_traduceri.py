"""Compileaza fisierele .po din locale/ in .mo (ce citeste Django), fara GNU gettext instalat.

Folosire (din folderul proiectului):  python scripts/compileaza_traduceri.py
Echivalent cu `python manage.py compilemessages`, care pe Windows cere gettext instalat separat.
Fisierele .mo sunt deja incluse in proiect; rulati scriptul doar daca modificati un .po.
"""
import ast
import struct
from pathlib import Path


def citeste_po(cale):
    """Returneaza {cheie: traducere}; cheia e msgid (cu context: 'ctx\\x04msgid', la plural: 'sg\\x00pl')."""
    intrari, curent, camp = {}, {}, None

    def salveaza():
        if "msgid" not in curent or curent.get("fuzzy"):
            return
        cheie = curent["msgid"]
        if "msgid_plural" in curent:
            cheie += "\0" + curent["msgid_plural"]
            forme = [curent[k] for k in sorted(k for k in curent if k.startswith("msgstr["))]
            valoare = "\0".join(forme)
        else:
            valoare = curent.get("msgstr", "")
        if "msgctxt" in curent:
            cheie = curent["msgctxt"] + "\x04" + cheie
        if valoare or cheie == "":
            intrari[cheie] = valoare

    for linie in Path(cale).read_text(encoding="utf-8").splitlines():
        linie = linie.strip()
        if linie.startswith("#,") and "fuzzy" in linie:
            curent["fuzzy"] = True
        if not linie or linie.startswith("#"):
            if not linie and curent:
                salveaza()
                curent, camp = {}, None
            continue
        if linie.startswith('"'):
            curent[camp] += ast.literal_eval(linie)
            continue
        cuvant, rest = linie.split(" ", 1)
        if cuvant in ("msgid", "msgctxt") and "msgstr" in "".join(curent):
            salveaza()
            curent = {}
        camp = cuvant
        curent[camp] = ast.literal_eval(rest)
    if curent:
        salveaza()
    return intrari


def scrie_mo(intrari, cale):
    chei = sorted(intrari)
    ids = [k.encode("utf-8") for k in chei]
    strs = [intrari[k].encode("utf-8") for k in chei]
    n = len(chei)
    inceput_ids = 7 * 4 + 16 * n
    offs_ids, offs_strs, date_ids, date_strs = [], [], b"", b""
    for i in ids:
        offs_ids.append((len(i), len(date_ids)))
        date_ids += i + b"\0"
    for s in strs:
        offs_strs.append((len(s), len(date_strs)))
        date_strs += s + b"\0"
    inceput_date_ids = inceput_ids
    inceput_date_strs = inceput_date_ids + len(date_ids)
    tabel = []
    for lungime, off in offs_ids:
        tabel += [lungime, off + inceput_date_ids]
    for lungime, off in offs_strs:
        tabel += [lungime, off + inceput_date_strs]
    antet = struct.pack("Iiiiiii", 0x950412DE, 0, n, 7 * 4, 7 * 4 + n * 8, 0, 0)
    Path(cale).write_bytes(antet + struct.pack(f"{len(tabel)}i", *tabel) + date_ids + date_strs)


if __name__ == "__main__":
    radacina = Path(__file__).resolve().parent.parent / "locale"
    for po in sorted(radacina.rglob("*.po")):
        intrari = citeste_po(po)
        scrie_mo(intrari, po.with_suffix(".mo"))
        print(f"{po.relative_to(radacina.parent)}: {len(intrari) - 1} traduceri -> {po.with_suffix('.mo').name}")
