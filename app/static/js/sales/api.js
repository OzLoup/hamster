const PRODUCTS_API_BASE = "/api/v1/products";
const SALES_API_BASE = "/api/v1/sales";

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
            message: "Request failed",
            details: null,
        };
    } catch {
        return {
            message: "Request failed",
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

export async function fetchProductsForSale() {
    const params = new URLSearchParams();
    params.set("page", "1");
    params.set("page_size", "100");

    const response = await fetch(`${PRODUCTS_API_BASE}?${params.toString()}`, {
        headers: {
            Accept: "application/json",
        },
    });

    await assertOk(response);
    const payload = await response.json();
    return payload.items || [];
}

export async function submitSale(payload) {
    const response = await fetch(SALES_API_BASE, {
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
