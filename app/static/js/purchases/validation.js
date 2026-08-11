function toNumber(value) {
    const num = Number(value);
    return Number.isFinite(num) ? num : NaN;
}

export function validateNewProductPayload(rawPayload) {
    const errors = [];

    const name = String(rawPayload.name || "").trim();
    const categoryId = Number(rawPayload.category_id);
    const cost = toNumber(rawPayload.cost);
    const salePrice = toNumber(rawPayload.sale_price);

    if (!name || name.length < 1 || name.length > 150) {
        errors.push("El nombre del producto debe tener entre 1 y 150 caracteres.");
    }

    if (!Number.isInteger(categoryId) || categoryId <= 0) {
        errors.push("Se requiere categoría.");
    }

    if (!Number.isFinite(cost) || cost < 0) {
        errors.push("El costo debe ser un número no negativo.");
    }

    if (!Number.isFinite(salePrice) || salePrice < 0) {
        errors.push("El precio de venta debe ser un número no negativo.");
    }

    return {
        isValid: errors.length === 0,
        errors,
        payload: {
            name,
            category_id: categoryId,
            stock_quantity: 0,
            cost: cost.toFixed(2),
            sale_price: salePrice.toFixed(2),
        },
    };
}

export function validatePurchaseInput({ supplierId, lines }) {
    const errors = [];

    if (!supplierId) {
        errors.push("Se requiere un proveedor.");
    }

    if (!Array.isArray(lines) || lines.length === 0) {
        errors.push("Agrega al menos una línea de producto antes de enviar la compra.");
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
