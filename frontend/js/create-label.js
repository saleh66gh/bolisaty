let senders = [];

async function loadSenders() {

    senders = await apiGet("/senders");

    const select = document.getElementById("sender_id");

    select.innerHTML = senders.map(s => `
        <option value="${s.id}">
            ${s.store_name} - ${s.sender_branch || ""}
        </option>
    `).join("");

    if (senders.length) {

        await senderChanged();

    }

}
async function senderChanged() {

    const senderId = Number(document.getElementById("sender_id").value);

    const sender = senders.find(s => s.id === senderId);

    if (!sender) return;

    const store = await apiGet(`/stores/${sender.store_id}`);

    const templateSelect = document.getElementById("template_id");

    if (!templateSelect) return;

    templateSelect.value = store.default_template_id ?? "";
}

function addProduct() {
  document.getElementById("productsArea").insertAdjacentHTML("beforeend", `
    <div class="grid-2 product-row">
      <input class="product-name" placeholder="اسم المنتج">
      <input class="product-qty" type="number" value="1" placeholder="العدد">
    </div>
  `);
}

async function createLabel() {
  const products = [...document.querySelectorAll(".product-row")].map(row => ({
    name: row.querySelector(".product-name").value,
    quantity: Number(row.querySelector(".product-qty").value)
  }));

  const data = {
    store_name: "بوليصتي",
    store_logo: null,
    sender_id: Number(document.getElementById("sender_id").value),
    order_number: document.getElementById("order_number").value,
    order_date: document.getElementById("order_date").value,
    template_id: Number(document.getElementById("template_id").value),
    receiver_country: document.getElementById("receiver_country").value,
    receiver_first_name: document.getElementById("receiver_first_name").value,
    receiver_last_name: document.getElementById("receiver_last_name").value,
    receiver_phone: document.getElementById("receiver_phone").value,
    receiver_city: document.getElementById("receiver_city").value,
    receiver_district: document.getElementById("receiver_district").value,
    receiver_address: document.getElementById("receiver_address").value,
    receiver_national_address: document.getElementById("receiver_national_address").value || null,

    shipment_count: Number(document.getElementById("shipment_count").value),
    weight: Number(document.getElementById("weight").value),
    cod_enabled: document.getElementById("cod_enabled").value === "true",
    cod_amount: Number(document.getElementById("cod_amount").value || 0),

    products,
    notes: document.getElementById("notes").value
  };

  const box = document.getElementById("result");

  try {
    const res = await apiPost("/create-label", data);
    box.style.display = "block";
    box.innerHTML = `
      <b>تم إنشاء الملصق بنجاح ✅</b><br><br>
      رقم الطلب: ${res.order_number}<br><br>
      <button class="btn" onclick="downloadPdf('${res.order_number}')">تحميل PDF</button>
    `;
  } catch (err) {
    box.style.display = "block";
    box.innerHTML = `<b>خطأ:</b><pre>${JSON.stringify(err, null, 2)}</pre>`;
  }
}
async function loadTemplates() {
    const templates = await apiGet("/label-templates/active");

    const select = document.getElementById("template_id");

    select.innerHTML = templates.map(t => `
        <option value="${t.id}">${t.name}</option>
    `).join("");
}
document.addEventListener("DOMContentLoaded", () => {
  loadSenders();
  loadTemplates();
});