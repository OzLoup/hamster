export function validateSaleInput({ paymentMethod, lines }) {
    const errors = [];

    if (!paymentMethod) {
        errors.push("Se requiere un método de pago.");
    }

    if (!Array.isArray(lines) || lines.length === 0) {
        errors.push("Agrega al menos una línea de producto antes de enviar la venta.");
    }

    return {
        isValid: errors.length === 0,
        errors,
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
