const endpoint = window.FLAXON_GRAPHQL_URL || "/graphql";
const state = { repositories: [] };
const $ = (selector) => document.querySelector(selector);

async function graphql(query, variables = {}) {
    const response = await fetch(endpoint, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ query, variables }),
    });
    const payload = await response.json();
    if (!response.ok || payload.errors) throw new Error(payload.errors?.[0]?.message || "GraphQL request failed");
    return payload.data;
}

function setStatus(message = "", error = false) {
    const element = $("#status");
    element.textContent = message;
    element.classList.toggle("error", error);
}

function renderRepositories(repositories) {
    $("#repo-count").textContent = repositories.length;
    $("#repositories").innerHTML = repositories.length ? repositories.map((repo) => `
        <article class="repo-card">
            <h2>${escapeHtml(repo.name)}</h2>
            <p>${escapeHtml(repo.description || "No description provided.")}</p>
            <div class="repo-meta"><span class="owner">${escapeHtml(repo.owner.login)}</span><button class="star" data-id="${repo.id}" type="button">★ ${repo.stars}</button></div>
        </article>`).join("") : "<p>No repositories found.</p>";
}

function escapeHtml(value) { return String(value).replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character])); }

async function loadRepositories(search = "") {
    setStatus("Loading repositories…");
    try {
        const data = await graphql(`query Repositories($search: String) { repositories(search: $search) { id name description stars owner { login } } }`, { search });
        state.repositories = data.repositories;
        renderRepositories(state.repositories);
        setStatus(`${state.repositories.length} repositories loaded`);
    } catch (error) { setStatus(error.message, true); }
}

$("#search").addEventListener("input", (event) => loadRepositories(event.target.value.trim()));
$("#new-repo").addEventListener("click", () => $("#repo-dialog").showModal());
$("#repo-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
        await graphql(`mutation Create($name: String $description: String) { createRepository(name: $name description: $description) { id } }`, { name: form.get("name"), description: form.get("description") });
        event.currentTarget.reset(); $("#repo-dialog").close(); await loadRepositories($("#search").value.trim());
    } catch (error) { setStatus(error.message, true); }
});
$("#repositories").addEventListener("click", async (event) => {
    const button = event.target.closest(".star"); if (!button) return;
    try { await graphql(`mutation Star($id: Int) { starRepository(id: $id) { id } }`, { id: Number(button.dataset.id) }); await loadRepositories($("#search").value.trim()); }
    catch (error) { setStatus(error.message, true); }
});
loadRepositories();
