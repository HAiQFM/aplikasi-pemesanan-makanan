(() => {
    // Highlight active nav link based on current path.
    const currentPath = window.location.pathname;
    document.querySelectorAll("nav a").forEach((link) => {
        const href = link.getAttribute("href");
        if (!href) return;
        if (href === currentPath || (href !== "/" && currentPath.startsWith(href))) {
            link.style.backgroundColor = "#bfe6e1";
            link.style.borderColor = "#84cbc3";
            link.style.fontWeight = "700";
        }
    });

    // Confirm delete actions.
    document.querySelectorAll("form").forEach((form) => {
        const action = form.getAttribute("action") || "";
        if (!action.includes("/delete")) return;
        form.addEventListener("submit", (event) => {
            const ok = window.confirm("Yakin ingin menghapus data ini?");
            if (!ok) event.preventDefault();
        });
    });

    // Simple formatting helper for price fields.
    document.querySelectorAll('input[name="price"]').forEach((input) => {
        input.addEventListener("blur", () => {
            const value = Number(input.value);
            if (!Number.isNaN(value) && input.value !== "") {
                input.value = value.toFixed(2);
            }
        });
    });
})();
