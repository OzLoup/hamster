import { ApiError, login } from "./api.js";

const form = document.getElementById("login-form");
const emailInput = document.getElementById("login-email");
const passwordInput = document.getElementById("login-password");
const errorBox = document.getElementById("login-error");
const submitButton = document.getElementById("login-submit");
const submitSpinner = document.getElementById("login-spinner");
const submitLabel = document.getElementById("login-submit-label");

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
        submitLabel.textContent = isSubmitting ? "Ingresando..." : "Iniciar sesión";
    }
}

function redirectTarget(currentUser) {
    if (currentUser.is_superuser) {
        return "/admin";
    }
    const params = new URLSearchParams(window.location.search);
    const next = params.get("next");
    if (next && next.startsWith("/")) {
        return next;
    }
    return currentUser.role === "seller" ? "/sales" : "/";
}

async function handleSubmit(event) {
    event.preventDefault();
    clearError();

    const email = emailInput?.value.trim() || "";
    const password = passwordInput?.value || "";

    if (!email || !password) {
        showError("Ingresa tu correo y contraseña.");
        return;
    }

    try {
        setSubmitting(true);
        const currentUser = await login({ email, password });
        window.location.href = redirectTarget(currentUser);
    } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
            showError("Correo o contraseña incorrectos.");
        } else {
            showError(error.message || "No se pudo iniciar sesión.");
        }
    } finally {
        setSubmitting(false);
    }
}

form?.addEventListener("submit", handleSubmit);
