// auth-guard.js
const token = localStorage.getItem("tinko_access_token");

if (!token) {
  window.location.href = "../index.html";
}
