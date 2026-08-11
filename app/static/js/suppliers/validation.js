export function validateSupplierPayload(rawPayload) {
    const errors = [];

    const name = String(rawPayload.name || "").trim();
    const contactName = String(rawPayload.contact_name || "").trim();
    const phone = String(rawPayload.phone || "").trim();
    const email = String(rawPayload.email || "").trim();

    if (!name || name.length < 1 || name.length > 150) {
        errors.push("El nombre del proveedor debe tener entre 1 y 150 caracteres.");
    }

    if (contactName.length > 150) {
        errors.push("El nombre de contacto no puede exceder los 150 caracteres.");
    }

    if (phone.length > 30) {
        errors.push("El teléfono no puede exceder los 30 caracteres.");
    }

    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        errors.push("El correo electrónico no es válido.");
    }

    return {
        isValid: errors.length === 0,
        errors,
        payload: {
            name,
            contact_name: contactName || null,
            phone: phone || null,
            email: email || null,
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
