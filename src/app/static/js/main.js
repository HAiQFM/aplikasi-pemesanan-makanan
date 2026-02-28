document.addEventListener("DOMContentLoaded", function () {
  setActiveNavLink();
  enhanceFlashMessages();
  preventDoubleSubmit();
});

function setActiveNavLink() {
  var currentPath = window.location.pathname;
  var links = document.querySelectorAll(".nav-links a");
  links.forEach(function (link) {
    var href = link.getAttribute("href");
    if (!href) return;
    if (href === currentPath) {
      link.classList.add("is-active");
    }
  });
}

function enhanceFlashMessages() {
  var flashes = document.querySelectorAll(".flash");
  flashes.forEach(function (flash) {
    var closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.className = "flash-close";
    closeBtn.setAttribute("aria-label", "Tutup notifikasi");
    closeBtn.textContent = "x";
    closeBtn.addEventListener("click", function () {
      flash.remove();
    });
    flash.appendChild(closeBtn);

    window.setTimeout(function () {
      if (flash && flash.parentNode) {
        flash.remove();
      }
    }, 4500);
  });
}

function preventDoubleSubmit() {
  var forms = document.querySelectorAll("form");
  forms.forEach(function (form) {
    form.addEventListener("submit", function () {
      var submitButton = form.querySelector("button[type='submit']");
      if (!submitButton) return;
      submitButton.dataset.originalLabel = submitButton.textContent;
      submitButton.textContent = "Memproses...";
      submitButton.disabled = true;
    });
  });
}
