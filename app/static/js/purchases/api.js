const PRODUCTS_API_BASE = "/api/v1/products";
const SUPPLIERS_API_BASE = "/api/v1/suppliers";
const PURCHASES_API_BASE = "/api/v1/purchases";

export class ApiError extends Error {
    constructor(message, status, details = null) {
        super(message);
        this.name = "ApiError";
        this.status = status;
        this.details = details;
    }
}

async function parseError(response) {
    try {
        const payload = await response.json();
        const detail = payload.detail;
        if (Array.isArray(detail)) {
            return {
                message: "Validación fallida.",
                details: detail,
            };
        }
        if (typeof detail === "string" && detail.trim()) {
            return {
                message: detail,
                details: null,
            };
        }
        return {
            message: "Error en la solicitud",
            details: null,
        };
    } catch {
        return {
            message: "Error en la solicitud",
            details: null,
        };
    }
}

async function assertOk(response) {
    if (response.ok) {
        return;
    }
    const parsed = await parseError(response);
    throw new ApiError(parsed.message, response.status, parsed.details);
}

export async function fetchProductsForPurchase() {
    const params = new URLSearchParams();
    params.set("page", "1");
    params.set("page_size", "100");
    params.set("is_active", "true");

    const response = await fetch(`${PRODUCTS_API_BASE}?${params.toString()}`, {
        headers: {
            Accept: "application/json",
        },
    });

    await assertOk(response);
    const payload = await response.json();
    return payload.items || [];
}

export async function fetchActiveSuppliers() {
    const params = new URLSearchParams();
    params.set("is_active", "true");

    const response = await fetch(`${SUPPLIERS_API_BASE}?${params.toString()}`, {
        headers: {
            Accept: "application/json",
        },
    });

    await assertOk(response);
    return response.json();
}

export async function submitPurchase(payload) {
    const response = await fetch(PURCHASES_API_BASE, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
        },
        body: JSON.stringify(payload),
    });

    await assertOk(response);
    return response.json();
}
