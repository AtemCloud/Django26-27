// Campurile de tip fisier afiseaza textul browserului ("Choose File / No file chosen" pe un browser in engleza).
// Le inlocuim cu un buton si un text in romana; inputul real ramane in pagina (ascuns), deci formularul merge la fel.
document.querySelectorAll('input[type="file"]').forEach(input => {
    const zona = document.createElement("div");
    zona.className = "fisier";
    const buton = document.createElement("label");
    buton.className = "alege-fisier";
    buton.htmlFor = input.id;
    buton.textContent = input.multiple ? "Alege fisierele" : "Alege fisierul";
    const nume = document.createElement("span");
    nume.className = "nume-fisier";
    zona.append(buton, nume);
    input.classList.add("fisier-ascuns");
    input.after(zona);

    const actualizeaza = () => {
        nume.textContent = input.files.length ? [...input.files].map(f => f.name).join(", ") : "Niciun fisier ales";
    };
    input.addEventListener("change", actualizeaza);
    if (input.form) input.form.addEventListener("reset", () => setTimeout(actualizeaza));
    actualizeaza();
});
