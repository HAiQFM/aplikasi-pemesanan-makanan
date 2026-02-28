"use strict";

(() => {
  const items = Array.from(document.querySelectorAll(".item[data-unit-price]"));
  const subtotalEl = document.getElementById("subtotal-value");
  const serviceFeeEl = document.getElementById("service-fee-value");
  const discountEl = document.getElementById("discount-value");
  const totalEl = document.getElementById("total-value");

  if (!items.length || !subtotalEl || !serviceFeeEl || !discountEl || !totalEl) {
    return;
  }

  const serviceFee = Number(serviceFeeEl.dataset.fee || 0);
  const discount = Number(discountEl.dataset.discount || 0);

  const formatRupiah = (value) =>
    new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      maximumFractionDigits: 0
    }).format(value);

  const updateTotals = () => {
    let subtotal = 0;

    items.forEach((item) => {
      const unitPrice = Number(item.dataset.unitPrice || 0);
      const qtyEl = item.querySelector("[data-qty]");
      const linePriceEl = item.querySelector("[data-line-price]");

      if (!qtyEl || !linePriceEl) {
        return;
      }

      const qty = Math.max(1, Number(qtyEl.textContent) || 1);
      const lineTotal = unitPrice * qty;
      subtotal += lineTotal;
      linePriceEl.textContent = formatRupiah(lineTotal);
    });

    const total = Math.max(0, subtotal + serviceFee - discount);

    subtotalEl.textContent = formatRupiah(subtotal);
    serviceFeeEl.textContent = formatRupiah(serviceFee);
    discountEl.textContent = `- ${formatRupiah(discount)}`;
    totalEl.textContent = formatRupiah(total);
  };

  items.forEach((item) => {
    const qtyEl = item.querySelector("[data-qty]");
    const minusBtn = item.querySelector('[data-action="decrease"]');
    const plusBtn = item.querySelector('[data-action="increase"]');

    if (!qtyEl || !minusBtn || !plusBtn) {
      return;
    }

    minusBtn.addEventListener("click", () => {
      const currentQty = Number(qtyEl.textContent) || 1;
      qtyEl.textContent = String(Math.max(1, currentQty - 1));
      updateTotals();
    });

    plusBtn.addEventListener("click", () => {
      const currentQty = Number(qtyEl.textContent) || 1;
      qtyEl.textContent = String(currentQty + 1);
      updateTotals();
    });
  });

  updateTotals();
})();
