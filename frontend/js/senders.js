let senders = [];
let stores = [];
let editingSenderId = null;

document.addEventListener("DOMContentLoaded", async () => {
  await loadStores();
  await loadSenders();

  const search = document.getElementById("senderSearch");
  if (search) {
    search.addEventListener("input", renderSenders);
  }
});

async function loadStores() {
  try {
    stores = await apiGet("/stores");
  } catch {
    stores = [];
  }
}

async function loadSenders() {
  senders = await apiGet("/senders");
  renderSenders();
}

function getStoreName(storeId) {
  const store = stores.find(s => s.id === storeId);
  return store ? `${store.store_name} - ${store.account_number}` : "-";
}

function renderSenders() {
  const tbody = document.getElementById("sendersTable");
  const searchValue = (document.getElementById("senderSearch")?.value || "").trim();

  if (!tbody) return;

  const filtered = senders.filter(s =>
    (s.merchant_name || "").includes(searchValue) ||
    (s.store_name || "").includes(searchValue) ||
    (s.store_phone || "").includes(searchValue) ||
    (s.sender_branch || "").includes(searchValue)
  );

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;color:#777">لا يوجد مرسلون</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(s => `
    <tr>
      <td>${s.id}</td>
      <td>${s.merchant_name}</td>
      <td>${s.store_name}</td>
      <td>${s.store_phone}</td>
      <td>${s.merchant_city || "-"}</td>
      <td>${s.sender_branch || "-"}</td>
      <td>${getStoreName(s.store_id)}</td>
      <td class="actions">
        <button class="btn-light" onclick='openSenderModal(${JSON.stringify(s)})'>تعديل</button>
        <button class="btn-light" onclick="deleteSender(${s.id})">حذف</button>
      </td>
    </tr>
  `).join("");
}

function openSenderModal(sender = null) {
  editingSenderId = sender ? sender.id : null;

  const role = getCurrentRole();
  const showStoreSelect = role === "owner" || role === "admin";

  openModal(editingSenderId ? "تعديل مرسل" : "إضافة مرسل", `
    <div class="grid-2">

      ${showStoreSelect ? `
        <select id="sender_store_id">
          <option value="">اختر المتجر</option>
          ${stores.map(store => `
            <option value="${store.id}" ${sender && sender.store_id === store.id ? "selected" : ""}>
              ${store.store_name} - ${store.account_number}
            </option>
          `).join("")}
        </select>
      ` : ""}

      <input id="merchant_name" placeholder="اسم التاجر" value="${sender?.merchant_name || ""}">
      <input id="store_name" placeholder="اسم المتجر على الملصق" value="${sender?.store_name || ""}">
      <input id="store_phone" placeholder="رقم المتجر / المرسل" value="${sender?.store_phone || ""}">
      <input id="merchant_city" placeholder="المدينة" value="${sender?.merchant_city || ""}">
      <input id="merchant_district" placeholder="الحي" value="${sender?.merchant_district || ""}">
      <input id="merchant_national_address" placeholder="العنوان الوطني" value="${sender?.merchant_national_address || ""}">
      <input id="sender_branch" placeholder="الفرع" value="${sender?.sender_branch || ""}">
    </div>

    <textarea id="merchant_address" placeholder="العنوان">${sender?.merchant_address || ""}</textarea>

    <button class="btn" onclick="saveSender()">
      ${editingSenderId ? "تحديث المرسل" : "حفظ المرسل"}
    </button>
  `);
}

async function saveSender() {
  const role = getCurrentRole();
  const payload = {
    merchant_name: document.getElementById("merchant_name").value.trim(),
    store_name: document.getElementById("store_name").value.trim(),
    store_phone: document.getElementById("store_phone").value.trim(),
    merchant_city: document.getElementById("merchant_city").value.trim() || null,
    merchant_district: document.getElementById("merchant_district").value.trim() || null,
    merchant_address: document.getElementById("merchant_address").value.trim() || null,
    merchant_national_address: document.getElementById("merchant_national_address").value.trim() || null,
    sender_branch: document.getElementById("sender_branch").value.trim() || null
  };

  if (role === "owner" || role === "admin") {
    const storeId = Number(document.getElementById("sender_store_id").value);

    if (!storeId) {
      alert("اختر المتجر");
      return;
    }

    payload.store_id = storeId;
  }

  if (!payload.merchant_name || !payload.store_name || !payload.store_phone) {
    alert("اسم التاجر واسم المتجر ورقم المرسل مطلوبة");
    return;
  }

  try {
    if (editingSenderId) {
      await apiPut(`/senders/${editingSenderId}`, payload);
    } else {
      await apiPost("/senders", payload);
    }

    closeModal();
    editingSenderId = null;
    await loadSenders();

  } catch (err) {
    console.error(err);
    alert(err.detail || "فشل حفظ المرسل");
  }
}

async function deleteSender(id) {
  if (!confirm("حذف المرسل؟")) return;

  try {
    await apiDelete(`/senders/${id}`);
    await loadSenders();
  } catch (err) {
    console.error(err);
    alert("فشل حذف المرسل");
  }
}