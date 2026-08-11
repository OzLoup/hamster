function fieldErrorClass(input) {
    input.classList.add("border-rose-500", "ring-rose-500/40");
    input.classList.remove("border-slate-700", "focus:border-brand-400", "focus:ring-brand-500/40");
}

function clearFieldErrorClass(input) {
    input.classList.remove("border-rose-500", "ring-rose-500/40");
    input.classList.add("border-slate-700", "focus:border-brand-400", "focus:ring-brand-500/40");
}

export function createCategoryModal() {
    const overlay = document.getElementById("category-modal-overlay");
    const panel = document.getElementById("category-modal-panel");
    const closeButton = document.getElementById("close-category-modal");
    const cancelButton = document.getElementById("cancel-category-modal");
    const title = document.getElementById("category-modal-title");
    const subtitle = document.getElementById("category-modal-subtitle");
    const categoryIdInput = document.getElementById("category-id");
    const form = document.getElementById("category-form");
    const errorBox = document.getElementById("category-modal-errors");
    const submitButton = document.getElementById("submit-category");
    const submitSpinner = document.getElementById("category-submit-spinner");
    const submitLabel = document.getElementById("category-submit-label");
    const fieldInputs = Array.from(document.querySelectorAll(".category-field"));

    const confirmOverlay = document.getElementById("category-confirm-overlay");
    const confirmPanel = document.getElementById("category-confirm-panel");
    const confirmMessage = document.getElementById("category-confirm-message");
    const confirmDeleteButton = document.getElementById("confirm-category-delete");
    const cancelDeleteButton = document.getElementById("cancel-category-delete");

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

    const fillForm = (category) => {
        if (!form) {
            return;
        }

        categoryIdInput.value = category?.id ? String(category.id) : "";
        form.elements.namedItem("name").value = category?.name || "";
        form.elements.namedItem("description").value = category?.description || "";
    };

    const setMode = (nextMode) => {
        mode = nextMode;
        if (!title || !subtitle || !submitLabel) {
            return;
        }
        if (mode === "edit") {
            title.textContent = "Editar categoría";
            subtitle.textContent = "Actualiza los detalles de la categoría.";
            submitLabel.textContent = "Guardar categoría";
            return;
        }
        title.textContent = "Crear categoría";
        subtitle.textContent = "Agrega una nueva categoría a tu catálogo.";
        submitLabel.textContent = "Guardar categoría";
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
            id: categoryIdInput.value,
            name: form.elements.namedItem("name").value,
            description: form.elements.namedItem("description").value,
        };
    };

    const askDelete = (categoryId, categoryName) => {
        deleteTargetId = categoryId;
        if (confirmMessage) {
            confirmMessage.textContent = `¿Estás seguro de que deseas eliminar '${categoryName}'?`;
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
        getCategoryId: () => Number(categoryIdInput.value),
        askDelete,
        hideConfirm,
        onConfirmDelete: (handler) => confirmDeleteButton?.addEventListener("click", () => handler(deleteTargetId)),
    };
}
