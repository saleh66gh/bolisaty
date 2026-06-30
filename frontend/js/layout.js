async function loadSidebar() {
    const placeholder = document.getElementById("sidebar-placeholder");
    if (!placeholder) return;

    const res = await fetch("components/sidebar.html");
    const html = await res.text();

    placeholder.innerHTML = html;

    setActiveNav();
    applyRoleUI();
}

async function loadTopbar() {
    const placeholder = document.getElementById("topbar-placeholder");
    if (!placeholder) return;

    const res = await fetch("components/topbar.html");
    const html = await res.text();

    placeholder.innerHTML = html;

    const user = getCurrentUserData();

    if (user) {
        const nameEl = document.getElementById("currentUserName");
        const roleEl = document.getElementById("currentUserRole");

        if (nameEl) nameEl.innerText = user.full_name || user.username;
        if (roleEl) roleEl.innerText = user.role;
    }

    setPageTitle();
}

function setActiveNav() {
    const page = window.location.pathname.split("/").pop().replace(".html", "");

    document.querySelectorAll(".nav a").forEach(link => {
        if (link.dataset.page === page) {
            link.classList.add("active");
        }
    });
}

function setPageTitle() {
    const page = window.location.pathname.split("/").pop();

    const titles = {
        "index.html": ["الرئيسية", "نظرة عامة على النظام"],
        "stores.html": ["المتاجر", "إدارة المتاجر والاشتراكات"],
        "users.html": ["المستخدمون", "إدارة مستخدمي النظام"],
        "create-label.html": ["إنشاء ملصق", "إنشاء بوليصة شحن جديدة"],
        "senders.html": ["المرسلين", "إدارة بيانات المرسلين والفروع"],
        "labels.html": ["قائمة الملصقات", "عرض وتحميل الملصقات"]
    };

    const data = titles[page] || ["بوليصتي", "لوحة التحكم"];

    const titleEl = document.getElementById("pageTitle");
    const subEl = document.getElementById("pageSubtitle");

    if (titleEl) titleEl.innerText = data[0];
    if (subEl) subEl.innerText = data[1];
}
async function loadModal() {
    const res = await fetch("components/modal.html");
    const html = await res.text();

    document.body.insertAdjacentHTML("beforeend", html);
}
document.addEventListener("DOMContentLoaded", () => {
    loadSidebar();
    loadTopbar();
    loadModal();
});