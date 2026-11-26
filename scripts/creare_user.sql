-- Lab 3 Task 2: utilizatorul cu care se conecteaza Django la baza de date.
--
-- VARIANTA NEON (baza de date din cloud): rulati in Neon -> SQL Editor, pe baza de date "ProiectDjango".
-- Inlocuiti parola cu una lunga si aleatoare (Neon refuza parolele slabe).
CREATE ROLE magazin_user WITH LOGIN PASSWORD 'inlocuieste-cu-o-parola-lunga-si-aleatoare';
-- PostgreSQL 16+: ca sa putem crea o schema detinuta de magazin_user, rolul curent trebuie sa poata face SET ROLE magazin_user
GRANT magazin_user TO CURRENT_USER WITH INHERIT FALSE, SET TRUE;
CREATE SCHEMA django AUTHORIZATION magazin_user;
GRANT CONNECT ON DATABASE "ProiectDjango" TO magazin_user;
ALTER ROLE magazin_user SET search_path = django, public;

-- VARIANTA LOCALA (PostgreSQL instalat pe PC, pgAdmin -> Query Tool, conectat ca postgres):
-- CREATE ROLE magazin_user WITH LOGIN PASSWORD 'parola';
-- CREATE DATABASE magazin_hw OWNER magazin_user;
-- \c magazin_hw
-- CREATE SCHEMA django AUTHORIZATION magazin_user;
-- ALTER ROLE magazin_user SET search_path = django, public;
