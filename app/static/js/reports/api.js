const PRODUCTS_API_BASE = "/api/v1/products";
const SALES_API_BASE = "/api/v1/sales";

class ApiError extends Error {
    constructor(message) {
        super(message);
        this.name = "ApiError";
    }
}

async function assertOk(response) {
    if (response.ok) {
        return;
    }

    try {
        const payload = await response.json();
        throw new ApiError(payload.detail || "No se pudieron obtener los datos de reportes.");
    } catch {
        throw new ApiError("No se pudieron obtener los datos de reportes.");
    }
}

export async function fetchProductsForReports() {
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

export async function fetchSalesForReports() {
    const response = await fetch(SALES_API_BASE, {
        headers: {
            Accept: "application/json",
        },
    });

    await assertOk(response);
    return response.json();
}

export { ApiError };
