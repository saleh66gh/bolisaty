async function loadDashboard() {
    const labels = await apiGet("/labels");
    const senders = await apiGet("/senders");

    document.getElementById("totalLabels").innerText = labels.length;
    document.getElementById("totalSenders").innerText = senders.length;
    document.getElementById("failedLabels").innerText =
        labels.filter(l => l.status === "failed").length;

    const today = new Date().toISOString().slice(0, 10);
    document.getElementById("todayLabels").innerText =
        labels.filter(l => String(l.created_at || "").slice(0, 10) === today).length;

    const tbody = document.getElementById("latestLabels");
    tbody.innerHTML = labels.slice(0, 5).map(l => `
        <tr>
            <td>${l.order_number}</td>
            <td>${l.customer_name}</td>
            <td>${l.customer_phone}</td>
            <td><span class="badge success">${l.status}</span></td>
        </tr>
    `).join("");
}

loadDashboard();