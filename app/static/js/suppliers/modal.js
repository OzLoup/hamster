function fieldErrorClass(input) {
    input.classList.add("border-rose-500", "ring-rose-500/40");
    input.classList.remove("border-slate-700", "focus:border-brand-400", "focus:ring-brand-500/40");
}

function clearFieldErrorClass(input) {
    input.classList.remove("border-rose-500", "ring-rose-500/40");
    input.classList.add("border-slate-700", "focus:border-brand-400", "focus:ring-brand-500/40");
}

export function createSupplierModal() {
    const overlay = document.getElementById("supplier-modal-overlay");
    const panel = document.getElementById("supplier-modal-panel");
    const closeButton = document.getElementById("close-supplier-modal");
    const cancelButton = document.getElementById("cancel-supplier-modal");
    const title = document.getElementById("supplier-modal-title");
    const subtitle = document.getElementById("supplier-modal-subtitle");
    const supplierIdInput = document.getElementById("supplier-id");
    const form = document.getElementById("supplier-form");
    const errorBox = document.getElementById("supplier-modal-errors");
    const submitButton = document.getElementById("submit-supplier");
    const submitSpinner = document.getElementById("supplier-submit-spinner");
    const submitLabel = document.getElementById("supplier-submit-label");
    const fieldInputs = Array.from(document.querySelectorAll(".supplier-field"));

    const confirmOverlay = document.getElementById("supplier-confirm-overlay");
    const confirmPanel = document.getElementById("supplier-confirm-panel");
    const confirmMessage = document.getElementById("supplier-confirm-message");
    const confirmDeleteButton = document.getElementById("confirm-supplier-delete");
    const cancelDeleteButton = document.getElementById("cancel-supplier-delete");

    let mode = "create";
    let deleteTargetId = null;

    const hide = () => {
        if (!overlay || !panel) {
            return;
        }
        overlay.classList.add("opacity-0");
        panel.classList.add("scale-95", "translate-y-4");
        setTimeout(() => {
            overlay.classList.add("hidden");
            overlay.classList.remove("flex");
        }, 180);
    };

    const show = () => {
        if (!overlay || !panel) {
            return;
        }
        overlay.classList.remove("hidden");
        overlay.classList.add("flex");
        requestAnimationFrame(() => {
            overlay.classList.remove("opacity-0");
            panel.classList.remove("scale-95", "translate-y-4");
        });
    };

    const hideConfirm = () => {
        if (!confirmOverlay || !confirmPanel) {
            return;
        }
        confirmOverlay.classList.add("opacity-0");
        confirmPanel.classList.add("scale-95", "translate-y-4");
        setTimeout(() => {
            confirmOverlay.classList.add("hidden");
            confirmOverlay.classList.remove("flex");
        }, 180);
    };

    const showConfirm = () => {
        if (!confirmOverlay || !confirmPanel) {
            return;
        }
        confirmOverlay.classList.remove("hidden");
        confirmOverlay.classList.add("flex");
        requestAnimationFrame(() => {
            confirmOverlay.classList.remove("opacity-0");
            confirmPanel.classList.remove("scale-95", "translate-y-4");
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

    const fillForm = (supplier) => {
        if (!form) {
            return;
        }

        supplierIdInput.value = supplier?.id ? String(supplier.id) : "";
        form.elements.namedItem("name").value = supplier?.name || "";
        form.elements.namedItem("contact_name").value = supplier?.contact_name || "";
        form.elements.namedItem("phone").value = supplier?.phone || "";
        form.elements.namedItem("email").value = supplier?.email || "";
    };

    const setMode = (nextMode) => {
        mode = nextMode;
        if (!title || !subtitle || !submitLabel) {
            return;
        }
        if (mode === "edit") {
            title.textContent = "Editar proveedor";
            subtitle.textContent = "Actualiza los detalles del proveedor.";
            submitLabel.textContent = "Guardar proveedor";
            return;
        }
        title.textContent = "Crear proveedor";
        subtitle.textContent = "Agrega un nuevo proveedor.";
        submitLabel.textContent = "Guardar proveedor";
    };

    const setSubmitting = (isSubmitting) => {
        if (!submitButton || !submitSpinner) {
            return;
        }
        submitButton.disabled = isSubmitting;
        submitSpinner.classList.toggle("hidden", !isSubmitting);
    };

    const getRawValues = () => {
        if (!form) {
            return {};
        }
        return {
            id: supplierIdInput.value,
            name: form.elements.namedItem("name").value,
            contact_name: form.elements.namedItem("contact_name").value,
            phone: form.elements.namedItem("phone").value,
            email: form.elements.namedItem("email").value,
        };
    };

    const askDelete = (supplierId, supplierName) => {
        deleteTargetId = supplierId;
        if (confirmMessage) {
            confirmMessage.textContent = `¿Estás seguro de que deseas eliminar '${supplierName}'?`;
        }
        showConfirm();
    };

    closeButton?.addEventListener("click", hide);
    cancelButton?.addEventListener("click", hide);
    overlay?.addEventListener("click", (event) => {
        if (event.target === overlay) {
            hide();
        }
    });

    cancelDeleteButton?.addEventListener("click", hideConfirm);
    confirmOverlay?.addEventListener("click", (event) => {
        if (event.target === confirmOverlay) {
            hideConfirm();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            if (overlay && !overlay.classList.contains("hidden")) {
                hide();
            }
            if (confirmOverlay && !confirmOverlay.classList.contains("hidden")) {
                hideConfirm();
            }
        }
    });

    return {
        form,
        show,
        hide,
        fillForm,
        setMode,
        setSubmitting,
        getRawValues,
        resetErrors,
        setErrorMessages,
        markInvalidFields,
        getMode: () => mode,
        getSupplierId: () => Number(supplierIdInput.value),
        askDelete,
        hideConfirm,
        onConfirmDelete: (handler) => confirmDeleteButton?.addEventListener("click", () => handler(deleteTargetId)),
    };
}
