// ── Mobile nav toggle ─────────────────────────
document.getElementById("navToggle").addEventListener("click", function () {
  document.querySelector(".nav-links").classList.toggle("open");
});

// ── Toast helper ──────────────────────────────
function showToast(message, type = "success") {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.className = `toast ${type}`;
  setTimeout(() => { toast.classList.add("hidden"); }, 3500);
}

// ── Close modal on backdrop click ─────────────
document.addEventListener("click", function (e) {
  if (e.target.classList.contains("modal-backdrop")) {
    e.target.classList.add("hidden");
  }
});

// ── Active nav highlight ──────────────────────
document.querySelectorAll(".nav-links a").forEach(link => {
  if (link.href === window.location.href) link.classList.add("active");
});