const API_BASE = "http://api.bolisaty.me";

function getToken() {
  return localStorage.getItem("bolisaty_token");
}

function authHeaders(json = true) {
  const headers = {};

  if (json) {
    headers["Content-Type"] = "application/json";
  }

  const token = getToken();

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  return headers;
}

function requireLogin() {
  const page = window.location.pathname.split("/").pop();

  if (page !== "login.html" && !getToken()) {
    window.location.href = "login.html";
  }
}

async function handleAuth(res) {
  if (res.status === 401) {
    localStorage.removeItem("bolisaty_token");
    localStorage.removeItem("user");
    window.location.href = "login.html";
    return false;
  }

  return true;
}

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: authHeaders(false)
  });

  if (!(await handleAuth(res))) return;

  return await res.json();
}

async function apiPost(path, data) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: authHeaders(true),
    body: JSON.stringify(data)
  });

  if (!(await handleAuth(res))) return;

  const result = await res.json();

  if (!res.ok) {
    throw result;
  }

  return result;
}

async function apiPut(path, data) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "PUT",
    headers: authHeaders(true),
    body: JSON.stringify(data)
  });

  if (!(await handleAuth(res))) return;

  const result = await res.json();

  if (!res.ok) {
    throw result;
  }

  return result;
}

async function apiDelete(path) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
    headers: authHeaders(false)
  });

  if (!(await handleAuth(res))) return;

  return await res.json();
}

function downloadPdf(orderNumber) {
  fetch(`${API_BASE}/download/${orderNumber}`, {
    headers: authHeaders(false)
  })
    .then(res => {
      if (!res.ok) throw new Error("Download failed");
      return res.blob();
    })
    .then(blob => {
      const url = window.URL.createObjectURL(blob);
      window.open(url, "_blank");
    });
}
async function getCurrentUser() {
  return await apiGet("/me");
}
function getCurrentUserData() {
    return JSON.parse(localStorage.getItem("user"));
}
function openModal(title, bodyHtml) {
    const overlay = document.getElementById("modalOverlay");
    const titleEl = document.getElementById("modalTitle");
    const bodyEl = document.getElementById("modalBody");

    if (!overlay || !titleEl || !bodyEl) return;

    titleEl.innerText = title;
    bodyEl.innerHTML = bodyHtml;
    overlay.classList.remove("hidden");
}

function closeModal() {
    const overlay = document.getElementById("modalOverlay");

    if (overlay) {
        overlay.classList.add("hidden");
    }
}
function getCurrentRole() {
    const user = getCurrentUserData();
    return user ? user.role : null;
}
async function apiPatch(path, data = null) {
  const options = {
    method: "PATCH",
    headers: authHeaders(true)
  };

  if (data) {
    options.body = JSON.stringify(data);
  }

  const res = await fetch(`${API_BASE}${path}`, options);

  if (!(await handleAuth(res))) return;

  const result = await res.json();

  if (!res.ok) {
    throw result;
  }

  return result;
}
function logout() {
  localStorage.removeItem("bolisaty_token");
  window.location.href = "login.html";
}
function applyRoleUI() {

    const role = getCurrentRole();

    if (!role) return;

    if (role !== "owner") {

        document.querySelectorAll("[data-owner-only]").forEach(el => {
            el.style.display = "none";
        });

    }

    if (role !== "owner" && role !== "admin") {

        document.querySelectorAll("[data-admin]").forEach(el => {
            el.style.display = "none";
        });

    }

}
requireLogin();