document.addEventListener("DOMContentLoaded", function () {
  setActiveNavLink();
  enhanceFlashMessages();
  preventDoubleSubmit();
  initLoginWarningModal();
  initHomeQuickMenu();
  initMenuAddForms();
  initCheckoutCart();
  initPromoBox();
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
    if (form.classList.contains("js-menu-add-form")) return;
    form.addEventListener("submit", function () {
      var submitButton = form.querySelector("button[type='submit']");
      if (!submitButton) return;
      submitButton.dataset.originalLabel = submitButton.textContent;
      submitButton.textContent = "Memproses...";
      submitButton.disabled = true;
    });
  });
}

var CART_STORAGE_KEY = "foodhall_cart";
var PROMO_STORAGE_KEY = "foodhall_promo_code";
var loginWarningController = null;

function isUserLoggedIn() {
  return document.body && document.body.getAttribute("data-is-logged-in") === "true";
}

function initLoginWarningModal() {
  var modal = document.querySelector("[data-role='login-warning-modal']");
  if (!modal) return;

  var dialog = modal.querySelector(".login-warning-dialog");
  var closeButtons = modal.querySelectorAll("[data-role='login-warning-close']");
  var hideTimer = null;

  function closeModal() {
    modal.classList.remove("is-visible");
    modal.classList.add("is-hiding");
    window.clearTimeout(hideTimer);
    hideTimer = window.setTimeout(function () {
      modal.hidden = true;
      modal.classList.remove("is-hiding");
    }, 220);
  }

  function openModal() {
    modal.hidden = false;
    modal.classList.remove("is-hiding");
    window.requestAnimationFrame(function () {
      modal.classList.add("is-visible");
    });
  }

  closeButtons.forEach(function (button) {
    button.addEventListener("click", closeModal);
  });

  modal.addEventListener("click", function (event) {
    if (event.target === modal) closeModal();
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && modal.classList.contains("is-visible")) {
      closeModal();
    }
  });

  loginWarningController = {
    open: openModal,
    close: closeModal,
    focusDialog: function () {
      if (dialog) dialog.focus();
    }
  };
}

function getCartItems() {
  try {
    var raw = localStorage.getItem(CART_STORAGE_KEY);
    if (!raw) return [];
    var parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(function (item) {
      return item && item.name && Number(item.price) > 0 && Number(item.qty) > 0;
    });
  } catch (error) {
    return [];
  }
}

function saveCartItems(items) {
  localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));
}

function getAppliedPromoCode() {
  return (localStorage.getItem(PROMO_STORAGE_KEY) || "").trim().toUpperCase();
}

function setAppliedPromoCode(code) {
  localStorage.setItem(PROMO_STORAGE_KEY, (code || "").trim().toUpperCase());
}

function clearAppliedPromoCode() {
  localStorage.removeItem(PROMO_STORAGE_KEY);
}

function formatRupiah(value) {
  return "Rp " + Number(value).toLocaleString("id-ID");
}

function cartSubtotal(items) {
  return items.reduce(function (total, item) {
    return total + Number(item.price) * Number(item.qty);
  }, 0);
}

function calculatePromoDiscount(subtotal) {
  if (getAppliedPromoCode() !== "GROUP5") return 0;
  return Math.round(subtotal * 0.2);
}

function addItemToCart(name, price) {
  var items = getCartItems();
  var existing = items.find(function (item) {
    return item.name === name;
  });

  if (existing) {
    existing.qty += 1;
  } else {
    items.push({ name: name, price: Number(price), qty: 1 });
  }

  saveCartItems(items);
}

function decrementItemFromCart(name) {
  var items = getCartItems();
  var index = items.findIndex(function (item) {
    return item.name === name;
  });
  if (index === -1) return;

  items[index].qty -= 1;
  if (items[index].qty <= 0) {
    items.splice(index, 1);
  }
  saveCartItems(items);
}

function renderHomeCartSummary() {
  var list = document.querySelector("[data-role='home-cart-list']");
  var total = document.querySelector("[data-role='home-cart-total']");
  if (!list || !total) return;

  var items = getCartItems();
  list.innerHTML = "";

  if (!items.length) {
    var empty = document.createElement("li");
    empty.textContent = "Keranjang masih kosong";
    list.appendChild(empty);
    total.textContent = "Total: Rp 0";
    return;
  }

  items.forEach(function (item) {
    var line = document.createElement("li");
    var name = document.createElement("span");
    name.textContent = item.name + " x" + item.qty;
    var price = document.createElement("strong");
    price.textContent = formatRupiah(Number(item.price) * Number(item.qty));
    line.appendChild(name);
    line.appendChild(price);
    list.appendChild(line);
  });

  total.textContent = "Total: " + formatRupiah(cartSubtotal(items));
}

function initHomeQuickMenu() {
  var quickCard = document.querySelector("[data-role='quick-food-hall']");
  if (!quickCard) return;

  var filters = quickCard.querySelectorAll("[data-role='quick-filters'] .chip");
  var products = quickCard.querySelectorAll(".product-box[data-category]");
  var addButtons = quickCard.querySelectorAll(".js-add-to-cart");
  var emptyState = quickCard.querySelector("[data-role='quick-empty']");
  var activeFilter = "all";

  if (!filters.length || !products.length) return;

  function renderFilteredProducts() {
    var visibleCount = 0;
    products.forEach(function (product) {
      var category = product.getAttribute("data-category");
      var shouldShow = activeFilter === "all" || category === activeFilter;
      product.style.display = shouldShow ? "flex" : "none";
      if (shouldShow) visibleCount += 1;
    });

    if (emptyState) emptyState.hidden = visibleCount > 0;
  }

  filters.forEach(function (filterButton) {
    filterButton.addEventListener("click", function () {
      activeFilter = filterButton.getAttribute("data-filter");

      filters.forEach(function (chip) {
        chip.classList.toggle("is-active", chip === filterButton);
      });
      renderFilteredProducts();
    });
  });

  addButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      var product = button.closest(".product-box");
      if (!product) return;
      var name = product.getAttribute("data-item-name");
      var price = Number(product.getAttribute("data-item-price"));
      if (!name || !price) return;

      addItemToCart(name, price);
      renderHomeCartSummary();
      button.textContent = "Ditambah";
      window.setTimeout(function () {
        button.textContent = "Tambah";
      }, 700);
    });
  });

  renderFilteredProducts();
  renderHomeCartSummary();
}

function initMenuAddForms() {
  var forms = document.querySelectorAll(".js-menu-add-form");
  if (!forms.length) return;

  forms.forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (!isUserLoggedIn()) {
        event.preventDefault();
        if (loginWarningController) {
          loginWarningController.open();
          window.setTimeout(function () {
            loginWarningController.focusDialog();
          }, 30);
        }
        return;
      }

      event.preventDefault();
      var name = form.getAttribute("data-item-name");
      var price = Number(form.getAttribute("data-item-price"));
      if (!name || !price) return;

      addItemToCart(name, price);

      var button = form.querySelector("button[type='submit']");
      if (!button) return;
      var originalLabel = button.textContent;
      button.textContent = "Ditambah";
      button.disabled = true;
      window.setTimeout(function () {
        button.textContent = originalLabel;
        button.disabled = false;
      }, 700);
    });
  });
}

function initCheckoutCart() {
  var cartList = document.querySelector("[data-role='checkout-cart-list']");
  if (!cartList) return;

  var subtotalTarget = document.querySelector("[data-role='checkout-subtotal']");
  var discountTarget = document.querySelector("[data-role='checkout-discount']");
  var totalTarget = document.querySelector("[data-role='checkout-total']");
  var form = document.querySelector("form[action*='/order/checkout']");
  var totalField = document.querySelector("input[name='order_total']");
  var itemsField = document.querySelector("input[name='checkout_items']");
  var deliveryFee = 12000;

  function renderCheckoutCart() {
    var items = getCartItems();
    cartList.innerHTML = "";

    if (!items.length) {
      var empty = document.createElement("article");
      empty.className = "cart-item";
      empty.innerHTML = "<div><p class='item-name'>Keranjang kosong</p><p class='item-price'>Tambahkan item dari beranda terlebih dahulu.</p></div>";
      cartList.appendChild(empty);
      if (form) form.querySelector("button[type='submit']").disabled = true;
      if (subtotalTarget) subtotalTarget.textContent = formatRupiah(0);
      if (discountTarget) discountTarget.textContent = "- " + formatRupiah(0);
      if (totalTarget) totalTarget.textContent = formatRupiah(0);
      if (totalField) totalField.value = "0";
      if (itemsField) itemsField.value = "[]";
      return;
    }

    items.forEach(function (item) {
      var row = document.createElement("article");
      row.className = "cart-item";
      row.innerHTML =
        "<div><p class='item-name'>" +
        item.name +
        "</p><p class='item-price'>" +
        formatRupiah(item.price * item.qty) +
        "</p></div><div class='checkout-item-actions'><span class='qty'>" +
        item.qty +
        "x</span><button type='button' class='trash-btn' data-action='decrement-item' data-item-name='" +
        item.name +
        "' aria-label='Kurangi item' title='Kurangi item'>&#128465;</button></div>";
      cartList.appendChild(row);
    });

    if (form) form.querySelector("button[type='submit']").disabled = false;
    var subtotal = cartSubtotal(items);
    var discount = calculatePromoDiscount(subtotal);
    var total = Math.max(0, subtotal + deliveryFee - discount);
    if (subtotalTarget) subtotalTarget.textContent = formatRupiah(subtotal);
    if (discountTarget) discountTarget.textContent = "- " + formatRupiah(discount);
    if (totalTarget) totalTarget.textContent = formatRupiah(total);
    if (totalField) totalField.value = String(total);
    if (itemsField) itemsField.value = JSON.stringify(items);
  }

  cartList.addEventListener("click", function (event) {
    var target = event.target;
    if (!(target instanceof Element)) return;
    if (target.getAttribute("data-action") !== "decrement-item") return;
    var name = target.getAttribute("data-item-name");
    if (!name) return;

    decrementItemFromCart(name);
    renderCheckoutCart();
    renderHomeCartSummary();
  });

  document.addEventListener("checkout:refresh", renderCheckoutCart);

  renderCheckoutCart();
}

function initPromoBox() {
  var openBtn = document.querySelector("[data-role='promo-open']");
  var panel = document.querySelector("[data-role='promo-panel']");
  if (!openBtn || !panel) return;

  var closeBtn = panel.querySelector("[data-role='promo-close']");
  var backBtn = panel.querySelector("[data-role='promo-back']");
  var clearBtn = panel.querySelector("[data-role='promo-clear']");
  var applyBtn = panel.querySelector("[data-role='promo-apply']");
  var input = panel.querySelector("[data-role='promo-input']");
  var message = panel.querySelector("[data-role='promo-message']");
  var validPromoCode = "GROUP5";

  function setPromoMessage(text, type) {
    if (!message) return;
    message.textContent = text;
    message.className = "promo-message" + (type ? " " + type : "");
  }

  function showPanel() {
    panel.hidden = false;
    setPromoMessage("", "");
    if (input) {
      input.value = getAppliedPromoCode();
      input.focus();
    }
  }

  function hidePanel() {
    panel.hidden = true;
  }

  openBtn.addEventListener("click", showPanel);
  if (closeBtn) closeBtn.addEventListener("click", hidePanel);
  if (backBtn) backBtn.addEventListener("click", hidePanel);

  if (clearBtn && input) {
    clearBtn.addEventListener("click", function () {
      input.value = "";
      setPromoMessage("", "");
      clearAppliedPromoCode();
      openBtn.textContent = "Apply";
      document.dispatchEvent(new Event("checkout:refresh"));
      input.focus();
    });
  }

  if (applyBtn && input) {
    applyBtn.addEventListener("click", function () {
      var code = input.value.trim();
      if (!code) {
        setPromoMessage("Kode promo wajib diisi.", "error");
        return;
      }

      if (code.toUpperCase() !== validPromoCode) {
        setPromoMessage("Kode promo tidak valid. Coba promo lain.", "error");
        return;
      }

      setPromoMessage("Kode promo berhasil diterapkan.", "success");
      setAppliedPromoCode(validPromoCode);
      openBtn.textContent = "Apply (" + validPromoCode + ")";
      document.dispatchEvent(new Event("checkout:refresh"));
      hidePanel();
    });
  }

  var activePromoCode = getAppliedPromoCode();
  if (activePromoCode) {
    openBtn.textContent = "Apply (" + activePromoCode + ")";
  }
}
