let users = [];
let stores = [];

document.addEventListener("DOMContentLoaded", async () => {
    await loadStores();
    await loadUsers();

    const search = document.getElementById("userSearch");
    if (search) {
        search.addEventListener("input", renderUsers);
    }
});

async function loadUsers() {
    users = await apiGet("/users");
    renderUsers();
}

async function loadStores() {
    try {
        stores = await apiGet("/stores");
    } catch {
        stores = [];
    }
}

function getStoreName(storeId) {
    const store = stores.find(s => s.id === storeId);
    return store ? `${store.store_name} (${store.account_number})` : "-";
}

function renderUsers() {
    const tbody = document.getElementById("usersTable");
    const searchValue = (document.getElementById("userSearch")?.value || "").trim();

    if (!tbody) return;

    const filtered = users.filter(user =>
        user.full_name.includes(searchValue) ||
        user.username.includes(searchValue) ||
        user.role.includes(searchValue) ||
        (user.phone || "").includes(searchValue)
    );

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;color:#777">لا يوجد مستخدمون</td></tr>`;
        return;
    }

    tbody.innerHTML = filtered.map(user => `
        <tr>
            <td>${user.full_name}</td>
            <td>${user.username}</td>
            <td>${user.role}</td>
            <td>${getStoreName(user.store_id)}</td>
            <td>${user.phone || "-"}</td>
            <td>
                <span class="badge ${user.is_active ? "success" : "danger"}">
                    ${user.is_active ? "نشط" : "موقوف"}
                </span>
            </td>
            <td>${user.last_login ? new Date(user.last_login).toLocaleString("ar-SA") : "-"}</td>
            <td class="actions">
                <button class="btn-light" onclick="deactivateUser(${user.id})">تعطيل</button>
            </td>
        </tr>
    `).join("");
}

function openUserModal() {
    openModal("إضافة مستخدم جديد", `
        <div class="grid-2">
            <input id="u_full_name" placeholder="الاسم الكامل">
            <input id="u_username" placeholder="اسم الدخول">
            <input id="u_password" type="password" placeholder="كلمة المرور">
            <input id="u_email" placeholder="البريد الإلكتروني">
            <input id="u_phone" placeholder="رقم الجوال">

            <select id="u_role" onchange="toggleStoreSelect()">
                <option value="admin">Admin</option>
                <option value="store_owner">صاحب متجر</option>
            </select>

            <select id="u_store_id" style="display:none">
                <option value="">اختر المتجر</option>
                ${stores.map(store => `
                    <option value="${store.id}">
                        ${store.store_name} - ${store.account_number}
                    </option>
                `).join("")}
            </select>
        </div>

        <button class="btn" onclick="createUser()">إضافة المستخدم</button>
    `);
}

function toggleStoreSelect() {
    const role = document.getElementById("u_role").value;
    const storeSelect = document.getElementById("u_store_id");

    if (role === "store_owner") {
        storeSelect.style.display = "block";
    } else {
        storeSelect.style.display = "none";
        storeSelect.value = "";
    }
}

async function createUser() {
    const role = document.getElementById("u_role").value;

    const payload = {
        full_name: document.getElementById("u_full_name").value.trim(),
        username: document.getElementById("u_username").value.trim(),
        password: document.getElementById("u_password").value.trim(),
        email: document.getElementById("u_email").value.trim() || null,
        phone: document.getElementById("u_phone").value.trim() || null,
        role: role,
        store_id: role === "store_owner"
            ? Number(document.getElementById("u_store_id").value)
            : null
    };

    if (!payload.full_name || !payload.username || !payload.password) {
        alert("الاسم واسم الدخول وكلمة المرور مطلوبة");
        return;
    }

    if (role === "store_owner" && !payload.store_id) {
        alert("اختر المتجر");
        return;
    }

    try {
        await apiPost("/users", payload);
        closeModal();
        await loadUsers();
        alert("تم إضافة المستخدم بنجاح");
    } catch (err) {
        console.error(err);
        alert(err.detail || "فشل إضافة المستخدم");
    }
}

async function deactivateUser(userId) {
    if (!confirm("هل تريد تعطيل هذا المستخدم؟")) return;

    try {
        await apiPatch(`/users/${userId}/status`);
        await loadUsers();
    } catch (err) {
        console.error(err);
        alert("فشل تعطيل المستخدم");
    }
}