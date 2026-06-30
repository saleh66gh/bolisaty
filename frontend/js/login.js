async function login() {
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  try {
    const result = await apiPost("/login", { username, password });

    localStorage.setItem("bolisaty_token", result.access_token);
    const user = await getCurrentUser();

    localStorage.setItem("user", JSON.stringify(user));
    window.location.href = "index.html";
  } catch (err) {
    document.getElementById("error").innerText = "بيانات الدخول غير صحيحة";
  }
}