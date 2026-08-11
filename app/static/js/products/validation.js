function toNumber(value) {
    const num = Number(value);
    return Number.isFinite(num) ? num : NaN;
}

export function validateProductPayload(rawPayload) {
    const errors = [];

    const name = String(rawPayload.name || "").trim();
    const categoryId = Number(rawPayload.category_id);
    const stockQuantity = toNumber(rawPayload.stock_quantity);
    const cost = toNumber(rawPayload.cost);
    const salePrice = toNumber(rawPayload.sale_price);

    if (!name || name.length < 1 || name.length > 150) {
        errors.push("El nombre del producto debe tener entre 1 y 150 caracteres.");
    }

    if (!Number.isInteger(categoryId) || categoryId <= 0) {
        errors.push("Se requiere categoría.");
    }

    if (!Number.isInteger(stockQuantity) || stockQuantity < 0) {
        errors.push("El stock debe ser un número entero no negativo.");
    }

    if (!Number.isFinite(cost) || cost < 0) {
        errors.push("El costo debe ser un número no negativo.");
    }

    if (!Number.isFinite(salePrice) || salePrice < 0) {
        errors.push("El precio de venta debe ser un número no negativo.");
    }

    const payload = {
        name,
        category_id: categoryId,
        stock_quantity: stockQuantity,
        cost: cost.toFixed(2),
        sale_price: salePrice.toFixed(2),
    };

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
