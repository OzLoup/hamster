function fieldErrorClass(input) {
    input.classList.add("border-rose-500", "ring-rose-500/40");
    input.classList.remove("border-slate-700", "focus:border-brand-400", "focus:ring-brand-500/40");
}

function clearFieldErrorClass(input) {
    input.classList.remove("border-rose-500", "ring-rose-500/40");
    input.classList.add("border-slate-700", "focus:border-brand-400", "focus:ring-brand-500/40");
}

export function createUserModal() {
    const overlay = document.getElementById("user-modal-overlay");
    const panel = document.getElementById("user-modal-panel");
    const closeButton = document.getElementById("close-user-modal");
    const cancelButton = document.getElementById("cancel-user-modal");
    const title = document.getElementById("user-modal-title");
    const subtitle = document.getElementById("user-modal-subtitle");
    const userIdInput = document.getElementById("user-id");
    const form = document.getElementById("user-form");
    const errorBox = document.getElementById("user-modal-errors");
    const submitButton = document.getElementById("submit-user");
    const submitSpinner = document.getElementById("user-submit-spinner");
    const submitLabel = document.getElementById("user-submit-label");
    const passwordInput = document.getElementById("user-password");
    const passwordHint = document.getElementById("user-password-hint");
    const roleSelect = document.getElementById("user-role");
    const fieldInputs = Array.from(document.querySelectorAll(".user-field"));

    const confirmOverlay = document.getElementById("user-confirm-overlay");
    const confirmPanel = document.getElementById("user-confirm-panel");
    const confirmTitle = document.getElementById("user-confirm-title");
    const confirmMessage = document.getElementById("user-confirm-message");
    const confirmActionButton = document.getElementById("confirm-user-action");
    const cancelConfirmButton = document.getElementById("cancel-user-confirm");

    let mode = "create";
    let confirmTargetId = null;

    if (window.currentUser?.role !== "admin") {
        roleSelect?.querySelector('option[value="admin"]')?.remove();
    }

    const hide = () => {
        if (!overlay || !panel) return;
        overlay.classList.add("opacity-0");
        panel.classList.add("scale-95", "translate-y-4");
        setTimeout(() => {
            overlay.classList.add("hidden");
            overlay.classList.remove("flex");
        }, 180);
    };

    const show = () => {
        if (!overlay || !panel) return;
        overlay.classList.remove("hidden");
        overlay.classList.add("flex");
        requestAnimationFrame(() => {
            overlay.classList.remove("opacity-0");
            panel.classList.remove("scale-95", "translate-y-4");
        });
    };

    const hideConfirm = () => {
        if (!confirmOverlay || !confirmPanel) return;
        confirmOverlay.classList.add("opacity-0");
        confirmPanel.classList.add("scale-95", "translate-y-4");
        setTimeout(() => {
            confirmOverlay.classList.add("hidden");
            confirmOverlay.classList.remove("flex");
        }, 180);
    };

    const showConfirm = () => {
        if (!confirmOverlay || !confirmPanel) return;
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
        if (!errorBox) return;
        errorBox.innerHTML = messages.map((message) => `<p>${message}</p>`).join("");
        errorBox.classList.remove("hidden");
    };

    const markInvalidFields = (messages) => {
        const lowerMessages = messages.map((item) => item.toLowerCase());
        fieldInputs.forEach((input) => {
            const key = input.getAttribute("name")?.toLowerCase();
            if (!key) return;
            if (lowerMessages.some((message) => message.includes(key))) {
                fieldErrorClass(input);
            }
        });
    };

    const fillForm = (user) => {
        if (!form) return;
        userIdInput.value = user?.id ? String(user.id) : "";
        form.elements.namedItem("full_name").value = user?.full_name || "";
        form.elements.namedItem("email").value = user?.email || "";
        form.elements.namedItem("role").value = user?.role || "seller";
        if (passwordInput) {
            passwordInput.value = "";
        }
    };

    const setMode = (nextMode) => {
        mode = nextMode;
        if (!title || !subtitle || !submitLabel) return;
        if (mode === "edit") {
            title.textContent = "Editar usuario";
            subtitle.textContent = "Actualiza los datos de acceso.";
            submitLabel.textContent = "Guardar cambios";
            if (passwordHint) {
                passwordHint.textContent = "Deja este campo vacío para mantener la contraseña actual.";
            }
            return;
        }
        title.textContent = "Nuevo usuario";
        subtitle.textContent = "Crea un acceso para tu equipo.";
        submitLabel.textContent = "Guardar usuario";
        if (passwordHint) {
            passwordHint.textContent = "Mínimo 8 caracteres.";
        }
    };

    const setSubmitting = (isSubmitting) => {
        if (!submitButton || !submitSpinner) return;
        submitButton.disabled = isSubmitting;
        submitSpinner.classList.toggle("hidden", !isSubmitting);
    };

    const getRawValues = () => {
        if (!form) return {};
        return {
            id: userIdInput.value,
            full_name: form.elements.namedItem("full_name").value,
            email: form.elements.namedItem("email").value,
            role: form.elements.namedItem("role").value,
            password: form.elements.namedItem("password").value,
        };
    };

    const askAction = (userId, userName, { isActive }) => {
        confirmTargetId = userId;
        const actionLabel = isActive ? "desactivar" : "activar";
        if (confirmTitle) {
            confirmTitle.textContent = isActive ? "Desactivar usuario" : "Activar usuario";
        }
        if (confirmMessage) {
            confirmMessage.textContent = `¿Estás seguro de que deseas ${actionLabel} a '${userName}'?`;
        }
        if (confirmActionButton) {
            confirmActionButton.textContent = isActive ? "Desactivar" : "Activar";
            confirmActionButton.classList.toggle("saas-btn-danger", isActive);
            confirmActionButton.classList.toggle("saas-btn-primary", !isActive);
        }
        showConfirm();
    };

    closeButton?.addEventListener("click", hide);
    cancelButton?.addEventListener("click", hide);
    overlay?.addEventListener("click", (event) => {
        if (event.target === overlay) hide();
    });

    cancelConfirmButton?.addEventListener("click", hideConfirm);
    confirmOverlay?.addEventListener("click", (event) => {
        if (event.target === confirmOverlay) hideConfirm();
    });

    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") return;
        if (overlay && !overlay.classList.contains("hidden")) hide();
        if (confirmOverlay && !confirmOverlay.classList.contains("hidden")) hideConfirm();
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
        getUserId: () => Number(userIdInput.value),
        askAction,
        hideConfirm,
        onConfirmAction: (handler) => confirmActionButton?.addEventListener("click", () => handler(confirmTargetId)),
    };
}
