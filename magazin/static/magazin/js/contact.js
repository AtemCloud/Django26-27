// Lab 5 Task 3: contor CNP, departamente dinamice, imagini aparute treptat, GDPR blocheaza submit
const formContact = document.getElementById("form-contact");
const cnp = document.getElementById("id_cnp");
const contor = document.getElementById("contor-cnp");
const tip = document.getElementById("id_tip_mesaj");
const departament = document.getElementById("id_departament");
const gdpr = document.getElementById("id_gdpr");
const trimite = document.getElementById("trimite-contact");

function actualizeazaContor() {
    const cifre = cnp.value.replace(/\D/g, "").length;
    contor.textContent = `${cifre}/13 cifre`;
    contor.classList.toggle("complet", cifre === 13);
}
cnp.addEventListener("input", actualizeazaContor);
actualizeazaContor();

// departamentele fiecarui tip de mesaj vin din baza de date (views.api_departamente)
let tipuri = {};
function incarcaDepartamente() {
    fetch(formContact.dataset.api)
        .then(response => response.json())
        .then(data => {
            tipuri = data;
            actualizeazaDepartamente();
        })
        .catch(error => console.error("Eroare la obtinerea departamentelor:", error));
}
function actualizeazaDepartamente() {
    const selectat = departament.value;
    departament.innerHTML = '<option value="neselectat">neselectat</option>';
    for (const d of (tipuri[tip.value]?.departamente || [])) {
        const opt = new Option(d.nume, d.id);
        departament.add(opt);
    }
    if ([...departament.options].some(o => o.value === selectat)) departament.value = selectat;
}
tip.addEventListener("change", actualizeazaDepartamente);
incarcaDepartamente();

const campuriImagini = [1, 2, 3].map(i => document.getElementById(`camp-imagine${i}`));
const inputuriImagini = [1, 2, 3].map(i => document.getElementById(`id_imagine${i}`));
function actualizeazaImagini() {
    let vizibil = true;
    inputuriImagini.forEach((input, i) => {
        campuriImagini[i].hidden = !vizibil;
        vizibil = vizibil && input.files.length > 0;
    });
    document.getElementById("max-imagini").hidden = !inputuriImagini.every(i => i.files.length > 0);
}
inputuriImagini.forEach(i => i.addEventListener("change", actualizeazaImagini));
actualizeazaImagini();

function actualizeazaGdpr() { trimite.disabled = !gdpr.checked; }
gdpr.addEventListener("change", actualizeazaGdpr);
formContact.addEventListener("reset", () => setTimeout(() => {
    actualizeazaGdpr(); actualizeazaContor(); actualizeazaDepartamente(); actualizeazaImagini();
}));
actualizeazaGdpr();
