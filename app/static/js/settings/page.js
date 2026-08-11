import { ApiError, fetchSettings, updateSettings } from "./api.js";

const form = document.getElementById("business-settings-form");
const businessNameInput = document.getElementById("business-name");
const errorBox = document.getElementById("settings-error");
const submitButton = document.getElementById("submit-business-settings");
const submitSpinner = document.getElementById("business-settings-submit-spinner");
const submitLabel = document.getElementById("business-settings-submit-label");

function notify(type, message, duration = 3200) {
    window.showToast?.({ type, message, duration });
}

function showError(message) {
    if (!errorBox) {
        return;
    }
    errorBox.textContent = message;
    errorBox.classList.remove("hidden");
}

function clearError() {
    if (!errorBox) {
        return;
    }
    errorBox.textContent = "";
    errorBox.classList.add("hidden");
}

function setSubmitting(isSubmitting) {
    if (submitButton) {
        submitButton.disabled = isSubmitting;
    }
    submitSpinner?.classList.toggle("hidden", !isSubmitting);
    if (submitLabel) {
        submitLabel.textContent = isSubmitting ? "Guardando..." : "Guardar cambios";
    }
}

async function loadSettings() {
    try {
        const current = await fetchSettings();
        if (businessNameInput) {
            businessNameInput.value = current.business_name;
        }
    } catch (error) {
        const message = error instanceof ApiError ? error.message : "No se pudo cargar la configuración.";
        showError(message);
        notify("error", message);
    }
}

async function handleSubmit(event) {
    event.preventDefault();
    clearError();

    const businessName = (businessNameInput?.value || "").trim();
    if (!businessName) {
        showError("El nombre del negocio no puede estar vacío.");
        notify("warning", "El nombre del negocio no puede estar vacío.");
        return;
    }

    try {
        setSubmitting(true);
        await updateSettings({ business_name: businessName });
        notify("success", "Configuración guardada correctamente.");
    } catch (error) {
        const message = error instanceof ApiError ? error.message : "No se pudo guardar la configuración.";
        showError(message);
        notify("error", message);
    } finally {
        setSubmitting(false);
    }
}

form?.addEventListener("submit", handleSubmit);
loadSettings();
