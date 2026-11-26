@ECHO OFF
REM Lab 6: backup al datelor din tabelele proprii (cele din models.py) sub forma de comenzi INSERT.
REM Folosire: scripts\backup.bat   (din folderul proiectului; pg_dump trebuie sa fie in PATH)
REM Datele de conectare se iau din .env (aceleasi ca pentru Django) sau din variabilele de mediu.

REM citim DB_HOST, DB_USER, DB_PASSWORD... din fisierul .env (daca exista)
IF EXIST .env FOR /F "usebackq eol=# tokens=1,* delims==" %%a IN (".env") DO SET "%%a=%%b"
IF NOT "%DB_SSLMODE%"=="" SET PGSSLMODE=%DB_SSLMODE%

IF "%DB_HOST%"=="" SET DB_HOST=localhost
IF "%DB_PORT%"=="" SET DB_PORT=5432
IF "%DB_USER%"=="" SET DB_USER=magazin
IF "%DB_NAME%"=="" SET DB_NAME=magazin_hw
IF "%DB_PASSWORD%"=="" SET /P DB_PASSWORD=Parola pentru %DB_USER%: 
SET PGPASSWORD=%DB_PASSWORD%
SET FISIER=backup_%DB_NAME%.sql
REM cu schema separata (de ex. django) numele tabelului trebuie prefixat: django.magazin_produs
SET PREFIX=public.
IF NOT "%DB_SCHEMA%"=="" SET PREFIX=%DB_SCHEMA%.

IF EXIST %FISIER% DEL %FISIER%
ECHO Realizam procesarea tabelelor...

REM ordinea conteaza: intai tabelele fara chei straine, apoi cele care depind de ele
FOR %%t IN (
    "magazin_categorie" "magazin_brand" "magazin_serviciuaditional" "magazin_produs" "magazin_produs_servicii"
    "magazin_istoricpret" "magazin_articolblog" "magazin_articolblog_produse"
    "magazin_utilizator" "magazin_utilizator_groups" "magazin_utilizator_user_permissions" "magazin_profil"
    "magazin_departament" "magazin_angajat" "magazin_tipmesaj" "magazin_tipmesaj_departamente"
    "magazin_comanda" "magazin_comandaprodus" "magazin_review" "magazin_favorit" "magazin_voucher"
) DO (
    ECHO Tabelul %%~t
    pg_dump --column-inserts --data-only --inserts -h %DB_HOST% -U %DB_USER% -p %DB_PORT% -d %DB_NAME% -t %PREFIX%%%~t >> %FISIER%
)

SET PGPASSWORD=
ECHO Gata: %FISIER%
