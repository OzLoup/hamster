export function validateCategoryPayload(rawPayload) {
    const errors = [];

    const name = String(rawPayload.name || "").trim();
    const description = String(rawPayload.description || "").trim();

    if (!name || name.length < 1 || name.length > 120) {
        errors.push("El nombre de la categoría debe tener entre 1 y 120 caracteres.");
    }

    if (description.length > 255) {
        errors.push("La descripción no puede exceder los 255 caracteres.");
    }

    return {
        isValid: errors.length === 0,
        errors,
        payload: {
            name,
            description: description || null,
        },
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
