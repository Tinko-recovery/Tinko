// logout.js

console.log("🚪 Logout script loaded");

function logout() {
  console.log("🔐 Logging out user...");
  localStorage.removeItem("tinko_access_token");
  window.location.href = "../index.html";   // back to login screen
}
