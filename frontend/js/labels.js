let allLabels = [];

async function loadLabels() {
  allLabels = await apiGet("/labels");
  renderLabels(allLabels);
}

function renderLabels(labels) {
  document.getElementById("labelsTable").innerHTML = labels.map(l => `
    <tr>
      <td>${l.order_number}</td>
      <td>${l.customer_name}</td>
      <td>${l.customer_phone}</td>
      <td>${l.payment_method === "cash" ? "دفع عند الاستلام" : "مدفوع"}</td>
      <td><span class="badge success">${l.status}</span></td>
      <td>${String(l.created_at || "").slice(0, 19)}</td>
      <td><button class="btn-light" onclick="downloadPdf('${l.order_number}')">تحميل</button></td>
      <td><button class="btn-light" onclick="deleteLabel('${l.order_number}')">حذف</button></td>
    </tr>
  `).join("");
}

function filterLabels() {
  const q = document.getElementById("search").value.trim();
  const filtered = allLabels.filter(l =>
    String(l.order_number).includes(q) ||
    String(l.customer_phone).includes(q) ||
    String(l.customer_name).includes(q)
  );
  renderLabels(filtered);
}

async function deleteLabel(orderNumber) {
  if (!confirm("حذف الملصق؟")) return;
  await apiDelete(`/labels/${orderNumber}`);
  loadLabels();
}

loadLabels();