function fieldErrorClass(input) {
    input.classList.add("border-rose-500", "ring-rose-500/40");
    input.classList.remove("border-slate-700", "focus:border-brand-400", "focus:ring-brand-500/40");
}

function clearFieldErrorClass(input) {
    input.classList.remove("border-rose-500", "ring-rose-500/40");
    input.classList.add("border-slate-700", "focus:border-brand-400", "focus:ring-brand-500/40");
}

export function createProductModal() {
    const overlay = document.getElementById("product-modal-overlay");
    const panel = document.getElementById("product-modal-panel");
    const closeButton = document.getElementById("close-product-modal");
    const cancelButton = document.getElementById("cancel-product-modal");
    const title = document.getElementById("product-modal-title");
    const subtitle = document.getElementById("product-modal-subtitle");
    const productIdInput = document.getElementById("product-id");
    const form = document.getElementById("product-form");
    const errorBox = document.getElementById("product-modal-errors");
    const submitButton = document.getElementById("submit-product");
    const submitSpinner = document.getElementById("product-submit-spinner");
    const submitLabel = document.getElementById("product-submit-label");
    const fieldInputs = Array.from(document.querySelectorAll(".product-field"));
    const categorySelect = document.getElementById("product-category");

    let mode = "create";

    const hide = () => {
        if (!overlay || !panel) {
            return;
        }
        overlay.classList.add("opacity-0");
        panel.classList.add("scale-95", "translate-y-4");
        setTimeout(() => overlay.classList.add("hidden"), 180);
    };

    const show = () => {
        if (!overlay || !panel) {
            return;
        }
        overlay.classList.remove("hidden");
        requestAnimationFrame(() => {
            overlay.classList.remove("opacity-0");
            panel.classList.remove("scale-95", "translate-y-4");
        });
    };

    const resetErrors = () => {
        if (errorBox) {
            errorBox.textContent = "";
            errorBox.classList.add("hidden");
        }
        fieldInputs.forEach(clearFieldErrorClass);
    };

    const setErrorMessages = (messages) => {
        if (!errorBox) {
            return;
        }
        errorBox.innerHTML = messages.map((message) => `<p>${message}</p>`).join("");
        errorBox.classList.remove("hidden");
    };

    const markInvalidFields = (messages) => {
        const lowerMessages = messages.map((item) => item.toLowerCase());
        fieldInputs.forEach((input) => {
            const key = input.getAttribute("name")?.toLowerCase();
            if (!key) {
                return;
            }
            if (lowerMessages.some((message) => message.includes(key))) {
                fieldErrorClass(input);
            }
        });
    };

    const fillForm = (product) => {
        if (!form) {
            return;
        }

        productIdInput.value = product?.id ? String(product.id) : "";
        form.elements.namedItem("name").value = product?.name || "";
        form.elements.namedItem("sku").value = product?.sku || "";
        form.elements.namedItem("category_id").value = product?.category_id ? String(product.category_id) : "";
        form.elements.namedItem("stock_quantity").value = product?.stock_quantity ?? 0;
        form.elements.namedItem("cost").value = product?.cost ?? "0.00";
        form.elements.namedItem("sale_price").value = product?.sale_price ?? "0.00";
    };

    const setMode = (nextMode) => {
        mode = nextMode;
        if (!title || !subtitle || !submitLabel) {
            return;
        }
        if (mode === "edit") {
            title.textContent = "Editar producto";
            subtitle.textContent = "Actualiza los detalles del producto.";
            submitLabel.textContent = "Guardar producto";
            return;
        }
        title.textContent = "Crear producto";
        subtitle.textContent = "Agrega un nuevo producto a tu catálogo.";
        submitLabel.textContent = "Guardar producto";
    };

    const setSubmitting = (isSubmitting) => {
        if (!submitButton || !submitSpinner) {
            return;
        }
        submitButton.disabled = isSubmitting;
        submitSpinner.classList.toggle("hidden", !isSubmitting);
    };

    const setCategories = (categories) => {
        if (!categorySelect) {
            return;
        }
        categorySelect.innerHTML = [
            '<option value="">Selecciona categoría</option>',
            ...categories.map((category) => `<option value="${category.id}">${category.name}</option>`),
        ].join("");
    };

    const getRawValues = () => {
        if (!form) {
            return {};
        }
        return {
            id: productIdInput.value,
            name: form.elements.namedItem("name").value,
            sku: form.elements.namedItem("sku").value,
            category_id: form.elements.namedItem("category_id").value,
            stock_quantity: form.elements.namedItem("stock_quantity").value,
            cost: form.elements.namedItem("cost").value,
            sale_price: form.elements.namedItem("sale_price").value,
        };
    };

    closeButton?.addEventListener("click", hide);
    cancelButton?.addEventListener("click", hide);
    overlay?.addEventListener("click", (event) => {
        if (event.target === overlay) {
            hide();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && overlay && !overlay.classList.contains("hidden")) {
            hide();
        }
    });

    return {
        form,
        show,
        hide,
        fillForm,
        setMode,
        setSubmitting,
        setCategories,
        getRawValues,
        resetErrors,
        setErrorMessages,
        markInvalidFields,
        getMode: () => mode,
        getProductId: () => Number(productIdInput.value),
    };
}
