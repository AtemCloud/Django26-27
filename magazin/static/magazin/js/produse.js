// Lab 5 Task 2: filtrare fara reincarcarea paginii (bonus, cu fetch) + confirmare la resetarea filtrelor
const zona = document.getElementById("zona-produse");
const form = document.getElementById("form-filtre");

function afiseazaMesaje(mesaje) {
    let lista = document.querySelector(".mesaje");
    if (!lista) {
        lista = document.createElement("ul");
        lista.className = "mesaje";
        document.querySelector("main").before(lista);
    }
    lista.innerHTML = "";
    mesaje.forEach(m => {
        const li = document.createElement("li");
        li.className = `mesaj mesaj-${m.tip}`;
        li.innerHTML = '<i class="icon"></i>';
        li.append(m.text);
        lista.appendChild(li);
    });
}

function obtineProduse(url, adaugaInIstoric = true) {
    fetch(url, {
            method: "GET",
            headers: {
                "X-Requested-With": "fetch"
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                zona.innerHTML = data.html;
                afiseazaMesaje(data.mesaje);
                if (adaugaInIstoric) history.pushState({}, "", url);
            }
        })
        .catch(error => {
            console.error("Eroare la obtinerea produselor:", error);
            window.location = url; // daca fetch esueaza, incarcam pagina normal
        });
}

if (form) {
    form.addEventListener("submit", (ev) => {
        ev.preventDefault();
        const params = new URLSearchParams(new FormData(form));
        for (const [k, v] of [...params.entries()]) if (v === "") params.delete(k);
        obtineProduse(`${location.pathname}?${params}`);
    });
    document.getElementById("reset-filtre").addEventListener("click", (ev) => {
        // confirmare: utilizatorul pierde filtrele deja puse
        if (confirm("Vei pierde toate filtrele setate. Continui?")) {
            window.location = ev.target.dataset.url;
        }
    });
}
document.addEventListener("click", (ev) => {
    const link = ev.target.closest("#zona-produse a[data-ajax], #zona-produse .taguri a");
    if (link) {
        ev.preventDefault();
        obtineProduse(link.href);
    }
});
window.addEventListener("popstate", () => obtineProduse(location.href, false));
