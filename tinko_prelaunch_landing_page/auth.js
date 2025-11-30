// --------------------------------
// CONFIGURATION & CONSTANTS
// --------------------------------
const API_BASE = (() => {
  const hostname = window.location.hostname;
  if (!hostname || hostname === 'localhost' || hostname === '127.0.0.1') {
    return "http://127.0.0.1:8000";
  }
  return 'https://tinko-clean-backend.onrender.com';
})();

const PROFILE_URL = `${API_BASE}/v1/customer/profile`;

console.log('Using API Base:', API_BASE);

// --------------------------------
// DOM ELEMENTS
// --------------------------------
const step1 = document.getElementById("step1");
const step2 = document.getElementById("step2");
const emailInput = document.getElementById("login_email");
const otpInput = document.getElementById("otp_code");
const sendOtpBtn = document.getElementById("sendOtpBtn");
const verifyOtpBtn = document.getElementById("verifyOtpBtn");
const resendOtp = document.getElementById("resendOtp");
const loginMessage = document.getElementById("loginMessage");

// Toggle Elements
const tabLogin = document.getElementById("tabLogin");
const tabSignup = document.getElementById("tabSignup");
const authHeader = document.getElementById("authHeader");

// State
let currentIntent = "login"; // "login" or "signup"

// --------------------------------
// TOGGLE LOGIC
// --------------------------------
if (tabLogin && tabSignup) {
  tabLogin.addEventListener("click", () => setMode("login"));
  tabSignup.addEventListener("click", () => setMode("signup"));
}

function setMode(mode) {
  currentIntent = mode;
  setMessage(""); // Clear errors

  if (mode === "login") {
    // UI: Active Login
    tabLogin.classList.add("bg-tinko-blue", "text-white");
    tabLogin.classList.remove("text-slate-300");

    tabSignup.classList.remove("bg-tinko-blue", "text-white");
    tabSignup.classList.add("text-slate-300");

    authHeader.textContent = "Welcome Back";
    sendOtpBtn.textContent = "Send Login OTP";
  } else {
    // UI: Active Signup
    tabSignup.classList.add("bg-tinko-blue", "text-white");
    tabSignup.classList.remove("text-slate-300");

    tabLogin.classList.remove("bg-tinko-blue", "text-white");
    tabLogin.classList.add("text-slate-300");

    authHeader.textContent = "Get Started";
    sendOtpBtn.textContent = "Create Account";
  }
}

// --------------------------------
// MESSAGE HELPER
// --------------------------------
function setMessage(msg, isError = false) {
  if (loginMessage) {
    loginMessage.textContent = msg;
    loginMessage.style.color = isError ? "#f87171" : "#34d399";
  }
}

// --------------------------------
// SEND OTP
// --------------------------------
if (sendOtpBtn) {
  sendOtpBtn.addEventListener("click", async () => {
    const email = emailInput?.value.trim();
    if (!email) return alert("Enter a valid email");

    sendOtpBtn.disabled = true;
    const originalText = sendOtpBtn.textContent;
    sendOtpBtn.textContent = "Sending...";

    try {
      const res = await fetch(`${API_BASE}/v1/auth/email/send-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, intent: currentIntent })
      });

      if (res.ok) {
        setMessage(`OTP sent! Check your email to ${currentIntent}.`);
        step1.classList.add("hidden");
        step2.classList.remove("hidden");
      } else {
        const data = await res.json();
        setMessage(data.detail || "Failed to send OTP.", true);
      }
    } catch (err) {
      console.error("SEND OTP ERROR:", err);
      setMessage(`Backend unreachable (${API_BASE}). Check API.`, true);
    } finally {
      sendOtpBtn.disabled = false;
      sendOtpBtn.textContent = originalText;
    }
  });
}

// --------------------------------
// VERIFY OTP
// --------------------------------
if (verifyOtpBtn) {
  verifyOtpBtn.addEventListener("click", async () => {
    const otp = otpInput?.value.trim();
    const email = emailInput?.value.trim();

    if (!otp) return alert("Enter OTP");

    verifyOtpBtn.disabled = true;
    verifyOtpBtn.textContent = "Verifying...";

    try {
      const res = await fetch(`${API_BASE}/v1/auth/email/verify-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, otp })
      });

      const data = await res.json();
      console.log("Verify OTP Response:", data);

      const accessToken = data.access_token;

      if (accessToken) {
        setMessage("Success! Redirecting...");
        await handlePostLoginRedirect(accessToken);
      } else {
        setMessage("Invalid OTP.", true);
      }
    } catch (err) {
      console.error("VERIFY OTP ERROR:", err);
      setMessage(`Backend unreachable (${API_BASE}). Check API.`, true);
    } finally {
      verifyOtpBtn.disabled = false;
      verifyOtpBtn.textContent = "Verify OTP";
    }
  });
}

// --------------------------------
// RESEND OTP
// --------------------------------
if (resendOtp) {
  resendOtp.addEventListener("click", () => {
    if (sendOtpBtn) sendOtpBtn.click();
  });
}

// --------------------------------
// REDIRECT AFTER LOGIN
// --------------------------------
async function handlePostLoginRedirect(token) {
  try {
    localStorage.setItem("tinko_access_token", token);

    const res = await fetch(PROFILE_URL, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + token
      }
    });

    if (res.ok) {
      // Profile exists -> Dashboard
      window.location.href = "dashboard/index.html";
    } else if (res.status === 404) {
      // Profile missing -> Onboarding
      window.location.href = "dashboard/onboarding.html";
    } else {
      // Fallback
      window.location.href = "dashboard/index.html";
    }
  } catch (err) {
    console.error("POST LOGIN REDIRECT ERROR:", err);
    window.location.href = "dashboard/index.html";
  }
}
