let templates = [];
let editingTemplateId = null;

document.addEventListener("DOMContentLoaded", () => {
  loadTemplates();

  const search = document.getElementById("templateSearch");
  if (search) {
    search.addEventListener("input", renderTemplates);
  }
});

async function loadTemplates() {
  templates = await apiGet("/label-templates");
  renderTemplates();
}

function renderTemplates() {
  const tbody = document.getElementById("templatesTable");
  const searchValue = (document.getElementById("templateSearch")?.value || "").trim();

  if (!tbody) return;

  const filtered = templates.filter(t =>
    (t.name || "").includes(searchValue)
  );

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:#777">لا توجد قوالب</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(t => `
    <tr>
      <td>${t.id}</td>
      <td>${t.name}</td>
      <td>
        <span class="badge ${t.is_active ? "success" : "danger"}">
          ${t.is_active ? "نشط" : "غير نشط"}
        </span>
      </td>
      <td>${t.updated_at ? new Date(t.updated_at).toLocaleString("ar-SA") : "-"}</td>
      <td class="actions">
        <button class="btn-light" onclick="openTemplateModal(${t.id})">تعديل</button>
        <button class="btn-light" onclick="deactivateTemplate(${t.id})">تعطيل</button>
      </td>
    </tr>
  `).join("");
}

function openTemplateModal(templateId = null) {
  editingTemplateId = templateId;

  const template = templates.find(t => t.id === templateId);

  openModal(editingTemplateId ? "تعديل قالب" : "قالب جديد", `
    <input id="template_name" placeholder="اسم القالب" value="${template?.name || ""}">

    <textarea id="template_html"
              placeholder="الصق كود HTML هنا"
              style="min-height:420px;font-family:monospace;direction:ltr;text-align:left">${template?.html_code || ""}</textarea>

    <button class="btn" onclick="saveTemplate()">
      ${editingTemplateId ? "تحديث القالب" : "حفظ القالب"}
    </button>
  `);
}

async function saveTemplate() {
  const payload = {
    name: document.getElementById("template_name").value.trim(),
    html_code: document.getElementById("template_html").value
  };

  if (!payload.name || !payload.html_code) {
    alert("اسم القالب وكود HTML مطلوبان");
    return;
  }

  try {
    if (editingTemplateId) {
      await apiPut(`/label-templates/${editingTemplateId}`, payload);
    } else {
      await apiPost("/label-templates", payload);
    }

    closeModal();
    editingTemplateId = null;
    await loadTemplates();

    alert("تم حفظ القالب بنجاح");
  } catch (err) {
    console.error(err);
    alert(err.detail || "فشل حفظ القالب");
  }
}

async function deactivateTemplate(templateId) {
  if (!confirm("هل تريد تعطيل هذا القالب؟")) return;

  try {
    await apiPatch(`/label-templates/${templateId}/status`);
    await loadTemplates();
  } catch (err) {
    console.error(err);
    alert("فشل تعطيل القالب");
  }
}