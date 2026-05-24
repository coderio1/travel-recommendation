const TOKEN_KEY = "tr_token";

// -- Helpers --

function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}
function setToken(t) {
    if (t) localStorage.setItem(TOKEN_KEY, t);
    else localStorage.removeItem(TOKEN_KEY);
}

async function api(path, { method = "GET", body, auth = false } = {}) {
    const headers = { "Content-Type": "application/json" };
    if (auth) {
        const t = getToken();
        if (t) headers["Authorization"] = `Bearer ${t}`;
    }
    const res = await fetch(path, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Request failed");
    }
    return res.status === 204 ? null : res.json();
}

function el(id) { return document.getElementById(id); }

// -- Tab switching --

el("tab-login").addEventListener("click", () => {
    el("tab-login").classList.add("active");
    el("tab-register").classList.remove("active");
    el("login-form").classList.remove("hidden");
    el("register-form").classList.add("hidden");
    el("auth-error").textContent = "";
});
el("tab-register").addEventListener("click", () => {
    el("tab-register").classList.add("active");
    el("tab-login").classList.remove("active");
    el("register-form").classList.remove("hidden");
    el("login-form").classList.add("hidden");
    el("auth-error").textContent = "";
});

// -- Auth flow --

async function showAuthenticatedUI() {
    el("auth-panel").classList.add("hidden");
    el("rec-panel").classList.remove("hidden");
    el("dashboard-panel").classList.remove("hidden");
    el("logout-btn").classList.remove("hidden");

    try {
        const me = await api("/api/auth/me", { auth: true });
        el("user-info").textContent = `Hello, ${me.name || me.email}`;
        await Promise.all([loadActivityTypes(), loadFavorites()]);
    } catch {
        setToken(null);
        showLoggedOutUI();
    }
}

function showLoggedOutUI() {
    el("auth-panel").classList.remove("hidden");
    el("rec-panel").classList.add("hidden");
    el("dashboard-panel").classList.add("hidden");
    el("logout-btn").classList.add("hidden");
    el("user-info").textContent = "";
    el("login-form").reset();
    el("register-form").reset();
    el("rec-form").reset();
    el("results").innerHTML = "";
    _allResults = [];
    _shownCount = 0;
}

el("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
        const data = await api("/api/auth/login", {
            method: "POST",
            body: { email: fd.get("email"), password: fd.get("password") },
        });
        setToken(data.access_token);
        await showAuthenticatedUI();
    } catch (err) {
        el("auth-error").textContent = err.message;
    }
});

el("register-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
        await api("/api/auth/register", {
            method: "POST",
            body: {
                email: fd.get("email"),
                name: fd.get("name") || null,
                password: fd.get("password"),
            },
        });
        // Auto-login after register
        const data = await api("/api/auth/login", {
            method: "POST",
            body: { email: fd.get("email"), password: fd.get("password") },
        });
        setToken(data.access_token);
        await showAuthenticatedUI();
    } catch (err) {
        el("auth-error").textContent = err.message;
    }
});

el("logout-btn").addEventListener("click", () => {
    setToken(null);
    showLoggedOutUI();
});

// -- Recommendation form --

async function loadActivityTypes() {
    const types = await api("/api/activities");
    const select = document.querySelector('select[name="activity_type_id"]');
    // Reset (keep the "Any" option)
    select.innerHTML = '<option value="">Any</option>';
    for (const t of types) {
        const opt = document.createElement("option");
        opt.value = t.id;
        opt.textContent = t.name;
        select.appendChild(opt);
    }
}

el("rec-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);

    // Build payload, omitting empty fields
    const payload = {};
    const num = (k) => {
        const v = fd.get(k);
        return v === "" || v === null ? null : Number(v);
    };
    const str = (k) => {
        const v = fd.get(k);
        return v === "" || v === null ? null : v;
    };
    payload.wanted_country = str("wanted_country");
    payload.wanted_area = str("wanted_area");
    payload.activity_type_id = num("activity_type_id");
    payload.vacation_start_month = num("vacation_start_month");
    payload.vacation_end_month = num("vacation_end_month");
    payload.preference = str("preference");

    el("results").innerHTML = "<p>Loading...</p>";
    try {
        const data = await api("/api/recommendations", {
            method: "POST",
            body: payload,
            auth: true,
        });
        renderResults(data.results);
    } catch (err) {
        el("results").innerHTML = `<p class="error">${err.message}</p>`;
    }
});

const PAGE_SIZE = 10;
let _allResults = [];
let _shownCount = 0;

function resultCardHtml(r) {
    return `
        <div class="result-card" data-da-id="${r.destination_activity_id}">
            <button class="fav-btn${r.is_favorited ? " active" : ""}"
                    title="${r.is_favorited ? "Remove from favourites" : "Save to favourites"}"
                    onclick="toggleFavorite(this, ${r.destination_activity_id})">
                ${r.is_favorited ? "★" : "☆"}
            </button>
            <span class="score">${r.match_score} pts</span>
            <div class="rank">#${r.rank_position}</div>
            <div class="name">${r.destination_name} — ${r.activity_name}</div>
            <div class="rank">${[r.country, r.area].filter(Boolean).join(" · ")}</div>
            <div class="reason">${r.reason || ""}</div>
        </div>
    `;
}

function renderResults(results) {
    _allResults = results;
    _shownCount = 0;
    el("results").innerHTML = "";
    if (!results.length) {
        el("results").innerHTML = "<p>No matches found. Try loosening your filters.</p>";
        return;
    }
    showMoreResults();
}

function showMoreResults() {
    const existing = el("load-more-btn");
    if (existing) existing.remove();

    const batch = _allResults.slice(_shownCount, _shownCount + PAGE_SIZE);
    el("results").insertAdjacentHTML("beforeend", batch.map(resultCardHtml).join(""));
    _shownCount += batch.length;

    if (_shownCount < _allResults.length) {
        const remaining = _allResults.length - _shownCount;
        el("results").insertAdjacentHTML(
            "beforeend",
            `<button id="load-more-btn" onclick="showMoreResults()">Load more (${remaining} remaining)</button>`,
        );
    }
}

// -- Favourites --

async function toggleFavorite(btn, destinationActivityId) {
    const isFav = btn.classList.contains("active");
    try {
        if (isFav) {
            await api(`/api/favorites/${destinationActivityId}`, { method: "DELETE", auth: true });
            btn.classList.remove("active");
            btn.textContent = "☆";
            btn.title = "Save to favourites";
        } else {
            await api("/api/favorites", {
                method: "POST",
                body: { destination_activity_id: destinationActivityId },
                auth: true,
            });
            btn.classList.add("active");
            btn.textContent = "★";
            btn.title = "Remove from favourites";
        }
        await loadFavorites();
    } catch (err) {
        alert(err.message);
    }
}

async function loadFavorites() {
    try {
        const favs = await api("/api/favorites", { auth: true });
        renderFavorites(favs);
    } catch {
        // silently skip — dashboard is non-critical
    }
}

function renderFavorites(favs) {
    if (!favs.length) {
        el("favorites-list").innerHTML = "<p class='muted'>No favourites saved yet.</p>";
        return;
    }
    el("favorites-list").innerHTML = favs
        .map(
            (f) => `
        <div class="fav-card">
            <div class="fav-card-info">
                <div class="name">${f.destination_name} — ${f.activity_name}</div>
                <div class="muted">${[f.country, f.area].filter(Boolean).join(" · ")}</div>
            </div>
            <button class="unfav-btn" title="Remove from favourites"
                    onclick="removeFavorite(this, ${f.destination_activity_id})">✕ Remove</button>
        </div>
    `,
        )
        .join("");
}

async function removeFavorite(btn, destinationActivityId) {
    btn.disabled = true;
    try {
        await api(`/api/favorites/${destinationActivityId}`, { method: "DELETE", auth: true });
        const resultStar = document.querySelector(`.result-card[data-da-id="${destinationActivityId}"] .fav-btn`);
        if (resultStar) {
            resultStar.classList.remove("active");
            resultStar.textContent = "☆";
            resultStar.title = "Save to favourites";
        }
        await loadFavorites();
    } catch (err) {
        btn.disabled = false;
        alert(err.message);
    }
}

// -- Bootstrap --

if (getToken()) {
    showAuthenticatedUI();
} else {
    showLoggedOutUI();
}
