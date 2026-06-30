let stores = [];
let wizardStep = 1;

let wizardData = {
    store: {},
    owner: {},
    sender: {}
};

document.addEventListener("DOMContentLoaded", () => {
    loadStores();

    const search = document.getElementById("storeSearch");
    if (search) {
        search.addEventListener("input", renderStores);
    }
});

async function loadStores() {
    stores = await apiGet("/stores");
    renderStores();
}

function formatDate(dateValue) {
    if (!dateValue) return "-";
    return new Date(dateValue).toLocaleDateString("ar-SA");
}

function toDateInputValue(dateValue) {
    if (!dateValue) return "";
    return String(dateValue).split("T")[0];
}

function getRemainingDays(endDate) {
    if (!endDate) return "-";

    const today = new Date();
    const end = new Date(endDate);

    today.setHours(0, 0, 0, 0);
    end.setHours(0, 0, 0, 0);

    const diff = end - today;
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24));

    return days >= 0 ? `${days} يوم` : "منتهي";
}

function renderStores() {
    const tbody = document.getElementById("storesTable");
    const searchValue = (document.getElementById("storeSearch")?.value || "").trim();

    if (!tbody) return;

    const filtered = stores.filter(store =>
        store.store_name.includes(searchValue) ||
        store.account_number.includes(searchValue) ||
        (store.owner_name || "").includes(searchValue) ||
        (store.phone || "").includes(searchValue)
    );

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="10" style="text-align:center;color:#777">لا توجد متاجر</td></tr>`;
        return;
    }

    tbody.innerHTML = filtered.map(store => {
        const used = store.labels_used || 0;
        const limit = store.label_limit || 0;
        const remaining = Math.max(limit - used, 0);

        return `
            <tr>
                <td>${store.account_number}</td>

                <td>
                    ${store.store_logo
                        ? `<img src="${store.store_logo}" style="width:42px;height:42px;object-fit:contain;border-radius:8px;background:#fff;border:1px solid #eee">`
                        : "-"
                    }
                </td>

                <td>${store.store_name}</td>
                <td>${store.owner_name}</td>
                <td>${store.phone || "-"}</td>
                <td>${store.subscription_plan}</td>

                <td>
                    <span class="badge ${store.subscription_status === "active" ? "success" : "danger"}">
                        ${store.subscription_status}
                    </span>
                    <br>
                    <small>من: ${formatDate(store.subscription_start)}</small>
                    <br>
                    <small>إلى: ${formatDate(store.subscription_end)}</small>
                    <br>
                    <small>المتبقي: ${getRemainingDays(store.subscription_end)}</small>
                </td>

                <td>${used} / ${limit}<br><small>المتبقي: ${remaining}</small></td>

                <td>
                    <span class="badge ${store.is_active ? "success" : "danger"}">
                        ${store.is_active ? "نشط" : "موقوف"}
                    </span>
                </td>

                <td class="actions">
                    <button class="btn-light" onclick="openEditStore(${store.id})">تعديل</button>
                    <button class="btn-light" onclick="deactivateStore(${store.id})">تعطيل</button>
                </td>
            </tr>
        `;
    }).join("");
}

function openStoreWizard() {
    wizardStep = 1;

    wizardData = {
        store: {},
        owner: {},
        sender: {}
    };

    openModal("إنشاء متجر جديد", `
        <div id="wizardContent"></div>

        <div class="modal-footer" style="display:flex;justify-content:space-between;margin-top:20px">
            <button class="btn-light" id="wizardPrevBtn" onclick="prevWizardStep()">السابق</button>
            <button class="btn" id="wizardNextBtn" onclick="nextWizardStep()">التالي</button>
        </div>
    `);

    renderWizardStep();
    updateWizardButtons();
}

function renderWizardStep() {
    const box = document.getElementById("wizardContent");
    if (!box) return;

    if (wizardStep === 1) {
        box.innerHTML = `
            <h3>1. بيانات المتجر</h3>

            <div class="grid-2">
                <input id="w_account_number" placeholder="رقم الحساب (5 خانات)" value="${wizardData.store.account_number || ""}">
                <input id="w_store_name" placeholder="اسم المتجر" value="${wizardData.store.store_name || ""}">
                <input id="w_owner_name" placeholder="اسم صاحب المتجر" value="${wizardData.store.owner_name || ""}">
                <input id="w_phone" placeholder="رقم الجوال" value="${wizardData.store.phone || ""}">
                <input id="w_email" placeholder="البريد الإلكتروني" value="${wizardData.store.email || ""}">
                <input id="w_store_logo" placeholder="رابط شعار المتجر" value="${wizardData.store.store_logo || ""}">

                <input id="w_subscription_start" type="date" value="${wizardData.store.subscription_start || ""}">
                <input id="w_subscription_end" type="date" value="${wizardData.store.subscription_end || ""}">

                <select id="w_subscription_plan">
                    <option value="trial" ${wizardData.store.subscription_plan === "trial" ? "selected" : ""}>تجريبي</option>
                    <option value="basic" ${wizardData.store.subscription_plan === "basic" ? "selected" : ""}>Basic</option>
                    <option value="pro" ${wizardData.store.subscription_plan === "pro" ? "selected" : ""}>Pro</option>
                </select>

                <input id="w_label_limit" type="number" placeholder="حد الملصقات" value="${wizardData.store.label_limit || 100}">
            </div>
        `;
    }

    if (wizardStep === 2) {
        box.innerHTML = `
            <h3>2. بيانات دخول صاحب المتجر</h3>

            <div class="grid-2">
                <input id="w_user_full_name" placeholder="اسم صاحب الحساب" value="${wizardData.owner.full_name || ""}">
                <input id="w_username" placeholder="اسم الدخول" value="${wizardData.owner.username || ""}">
                <input id="w_password" type="password" placeholder="كلمة المرور" value="${wizardData.owner.password || ""}">
                <input id="w_user_email" placeholder="بريد المستخدم" value="${wizardData.owner.email || ""}">
                <input id="w_user_phone" placeholder="جوال المستخدم" value="${wizardData.owner.phone || ""}">
            </div>
        `;
    }

    if (wizardStep === 3) {
        box.innerHTML = `
            <h3>3. بيانات الفرع الرئيسي / المرسل</h3>

            <div class="grid-2">
                <input id="w_sender_merchant_name" placeholder="اسم التاجر" value="${wizardData.sender.merchant_name || ""}">
                <input id="w_sender_store_name" placeholder="اسم المتجر على الملصق" value="${wizardData.sender.store_name || ""}">
                <input id="w_sender_phone" placeholder="جوال المرسل" value="${wizardData.sender.store_phone || ""}">
                <input id="w_sender_branch" placeholder="اسم الفرع" value="${wizardData.sender.sender_branch || ""}">
                <input id="w_sender_city" placeholder="المدينة" value="${wizardData.sender.merchant_city || ""}">
                <input id="w_sender_district" placeholder="الحي" value="${wizardData.sender.merchant_district || ""}">
                <input id="w_sender_national_address" placeholder="العنوان الوطني" value="${wizardData.sender.merchant_national_address || ""}">
            </div>

            <textarea id="w_sender_address" placeholder="عنوان المرسل التفصيلي">${wizardData.sender.merchant_address || ""}</textarea>
        `;
    }
}

function updateWizardButtons() {
    const prevBtn = document.getElementById("wizardPrevBtn");
    const nextBtn = document.getElementById("wizardNextBtn");

    if (prevBtn) {
        prevBtn.disabled = wizardStep === 1;
        prevBtn.style.opacity = wizardStep === 1 ? "0.5" : "1";
    }

    if (nextBtn) {
        nextBtn.innerText = wizardStep === 3 ? "إنشاء المتجر" : "التالي";
    }
}

function saveCurrentWizardStep() {
    if (wizardStep === 1) {
        wizardData.store = {
            account_number: document.getElementById("w_account_number").value.trim(),
            store_name: document.getElementById("w_store_name").value.trim(),
            owner_name: document.getElementById("w_owner_name").value.trim(),
            email: document.getElementById("w_email").value.trim() || null,
            phone: document.getElementById("w_phone").value.trim() || null,
            store_logo: document.getElementById("w_store_logo").value.trim() || null,
            subscription_start: document.getElementById("w_subscription_start").value || null,
            subscription_end: document.getElementById("w_subscription_end").value || null,
            subscription_plan: document.getElementById("w_subscription_plan").value,
            subscription_status: "active",
            label_limit: Number(document.getElementById("w_label_limit").value || 100)
        };

        if (!wizardData.store.account_number || wizardData.store.account_number.length !== 5) {
            alert("رقم الحساب يجب أن يكون 5 خانات");
            return false;
        }

        if (!wizardData.store.store_name || !wizardData.store.owner_name) {
            alert("اسم المتجر واسم صاحب المتجر مطلوبان");
            return false;
        }
    }

    if (wizardStep === 2) {
        wizardData.owner = {
            full_name: document.getElementById("w_user_full_name").value.trim(),
            username: document.getElementById("w_username").value.trim(),
            password: document.getElementById("w_password").value.trim(),
            email: document.getElementById("w_user_email").value.trim() || null,
            phone: document.getElementById("w_user_phone").value.trim() || null,
            role: "store_owner",
            store_id: null
        };

        if (!wizardData.owner.full_name || !wizardData.owner.username || !wizardData.owner.password) {
            alert("اسم صاحب الحساب واسم الدخول وكلمة المرور مطلوبة");
            return false;
        }
    }

    if (wizardStep === 3) {
        wizardData.sender = {
            merchant_name: document.getElementById("w_sender_merchant_name").value.trim(),
            store_name: document.getElementById("w_sender_store_name").value.trim(),
            store_phone: document.getElementById("w_sender_phone").value.trim(),
            merchant_city: document.getElementById("w_sender_city").value.trim() || null,
            merchant_district: document.getElementById("w_sender_district").value.trim() || null,
            merchant_address: document.getElementById("w_sender_address").value.trim() || null,
            merchant_national_address: document.getElementById("w_sender_national_address").value.trim() || null,
            sender_branch: document.getElementById("w_sender_branch").value.trim() || null,
            store_logo: null,
            store_id: null
        };

        if (!wizardData.sender.merchant_name || !wizardData.sender.store_name || !wizardData.sender.store_phone) {
            alert("اسم التاجر واسم المتجر وجوال المرسل مطلوبة");
            return false;
        }
    }

    return true;
}

function nextWizardStep() {
    const saved = saveCurrentWizardStep();
    if (!saved) return;

    if (wizardStep < 3) {
        wizardStep++;
        renderWizardStep();
        updateWizardButtons();
        return;
    }

    submitStoreWizard();
}

function prevWizardStep() {
    saveCurrentWizardStep();

    if (wizardStep > 1) {
        wizardStep--;
        renderWizardStep();
        updateWizardButtons();
    }
}

async function submitStoreWizard() {
    try {
        await apiPost("/stores/create-full", wizardData);

        closeModal();
        await loadStores();

        alert("تم إنشاء المتجر وصاحب المتجر والمرسل بنجاح");
    } catch (err) {
        console.error(err);
        alert(err.detail || "فشل إنشاء المتجر");
    }
}
async function loadTemplateOptions(selected = null) {

    const templates = await apiGet("/label-templates/active");

    const select = document.getElementById("edit_default_template");

    if (!select) return;

    select.innerHTML = templates.map(t => `
        <option value="${t.id}" ${selected == t.id ? "selected" : ""}>
            ${t.name}
        </option>
    `).join("");

}
function openEditStore(storeId) {
    const store = stores.find(s => s.id === storeId);
    if (!store) return;

    openModal("تعديل المتجر", `
        <div class="grid-2">
            <input id="edit_store_name" placeholder="اسم المتجر" value="${store.store_name || ""}">
            <input id="edit_owner_name" placeholder="اسم صاحب المتجر" value="${store.owner_name || ""}">
            <input id="edit_phone" placeholder="رقم الجوال" value="${store.phone || ""}">
            <input id="edit_email" placeholder="البريد الإلكتروني" value="${store.email || ""}">
            <input id="edit_store_logo" placeholder="رابط الشعار" value="${store.store_logo || ""}">

            <select id="edit_subscription_plan">
                <option value="trial" ${store.subscription_plan === "trial" ? "selected" : ""}>تجريبي</option>
                <option value="basic" ${store.subscription_plan === "basic" ? "selected" : ""}>Basic</option>
                <option value="pro" ${store.subscription_plan === "pro" ? "selected" : ""}>Pro</option>
            </select>

            <select id="edit_subscription_status">
                <option value="active" ${store.subscription_status === "active" ? "selected" : ""}>نشط</option>
                <option value="inactive" ${store.subscription_status === "inactive" ? "selected" : ""}>غير نشط</option>
                <option value="expired" ${store.subscription_status === "expired" ? "selected" : ""}>منتهي</option>
            </select>

            <input id="edit_subscription_start" type="date" value="${toDateInputValue(store.subscription_start)}">
            <input id="edit_subscription_end" type="date" value="${toDateInputValue(store.subscription_end)}">
            <input id="edit_label_limit" type="number" placeholder="حد الملصقات" value="${store.label_limit || 100}">
            <label>القالب الافتراضي</label>
            <select id="edit_default_template"></select>
        </div>

        <button class="btn" onclick="saveStoreEdit(${store.id})">حفظ التعديل</button>
    `);
    loadTemplateOptions(store.default_template_id);
}

async function saveStoreEdit(storeId) {
    const payload = {
        store_name: document.getElementById("edit_store_name").value.trim(),
        owner_name: document.getElementById("edit_owner_name").value.trim(),
        phone: document.getElementById("edit_phone").value.trim() || null,
        email: document.getElementById("edit_email").value.trim() || null,
        store_logo: document.getElementById("edit_store_logo").value.trim() || null,
        subscription_plan: document.getElementById("edit_subscription_plan").value,
        subscription_status: document.getElementById("edit_subscription_status").value,
        subscription_start: document.getElementById("edit_subscription_start").value || null,
        subscription_end: document.getElementById("edit_subscription_end").value || null,
        label_limit: Number(document.getElementById("edit_label_limit").value || 100),
        default_template_id:Number(document.getElementById("edit_default_template").value)
    };

    if (!payload.store_name || !payload.owner_name) {
        alert("اسم المتجر واسم صاحب المتجر مطلوبان");
        return;
    }

    try {
        await apiPut(`/stores/${storeId}`, payload);

        closeModal();
        await loadStores();

        alert("تم تعديل بيانات المتجر");
    } catch (err) {
        console.error(err);
        alert(err.detail || "فشل تعديل المتجر");
    }
}

async function deactivateStore(storeId) {
    if (!confirm("هل تريد تعطيل هذا المتجر؟")) return;

    try {
        await apiPatch(`/stores/${storeId}/status`);
        await loadStores();
    } catch (err) {
        console.error(err);
        alert("فشل تعطيل المتجر");
    }
}