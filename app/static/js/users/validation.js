const VALID_ROLES = ["admin", "coordinator", "seller"];

export function validateUserPayload(rawPayload, { isCreate }) {
    const errors = [];

    const fullName = String(rawPayload.full_name || "").trim();
    const email = String(rawPayload.email || "").trim();
    const role = String(rawPayload.role || "");
    const password = String(rawPayload.password || "");

    if (!fullName || fullName.length > 150) {
        errors.push("El nombre completo debe tener entre 1 y 150 caracteres.");
    }

    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        errors.push("El correo electrónico no es válido.");
    }

    if (!VALID_ROLES.includes(role)) {
        errors.push("Selecciona un rol válido.");
    }

    if (isCreate && password.length < 8) {
        errors.push("La contraseña debe tener al menos 8 caracteres.");
    } else if (password && password.length < 8) {
        errors.push("La contraseña debe tener al menos 8 caracteres.");
    }

    const payload = {
        full_name: fullName,
        email,
        role,
    };
    if (password) {
        payload.password = password;
    }

    return {
        isValid: errors.length === 0,
        errors,
        payload,
    };
}

export function formatFastApiValidation(details) {
    if (!Array.isArray(details)) {
        return [];
    }

    return details.map((error) => {
        const path = Array.isArray(error.loc) ? error.loc.slice(1).join(".") : "field";
        return `${path}: ${error.msg}`;
    });
}
