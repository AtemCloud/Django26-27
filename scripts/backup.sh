#!/bin/sh
# Echivalentul lui backup.bat pentru Linux/macOS (citeste .env daca exista).
[ -f .env ] && export $(grep -v '^#' .env | tr -d '\r' | xargs)  # in Codespaces variabilele vin din secrets
FISIER="backup_${DB_NAME:-magazin_hw}.sql"
rm -f "$FISIER"
export PGPASSWORD="$DB_PASSWORD"
[ -n "$DB_SSLMODE" ] && export PGSSLMODE="$DB_SSLMODE"
for t in magazin_categorie magazin_brand magazin_serviciuaditional magazin_produs magazin_produs_servicii \
         magazin_istoricpret magazin_articolblog magazin_articolblog_produse magazin_utilizator \
         magazin_utilizator_groups magazin_utilizator_user_permissions magazin_profil magazin_departament \
         magazin_angajat magazin_tipmesaj magazin_tipmesaj_departamente magazin_comanda magazin_comandaprodus \
         magazin_review magazin_favorit magazin_voucher; do
  echo "Tabelul $t"
  pg_dump --column-inserts --data-only --inserts -h "${DB_HOST:-localhost}" -U "${DB_USER:-magazin}" \
          -p "${DB_PORT:-5432}" -d "${DB_NAME:-magazin_hw}" -t "${DB_SCHEMA:-public}.$t" >> "$FISIER"
done
echo "Gata: $FISIER"
