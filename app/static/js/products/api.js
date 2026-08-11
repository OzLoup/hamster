const PRODUCTS_API_BASE = "/api/v1/products";
const CATEGORIES_API_BASE = "/api/v1/categories";

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

export async function fetchProducts({ page, pageSize, search, categoryId, stockLevel, isActive, sortBy, sortDir }) {
    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("page_size", String(pageSize));
    if (search) {
        params.set("search", search);
    }
    if (categoryId) {
        params.set("category_id", String(categoryId));
    }
    if (stockLevel) {
        params.set("stock_level", stockLevel);
    }
    if (isActive) {
        params.set("is_active", isActive);
    }
    if (sortBy) {
        params.set("sort_by", sortBy);
        params.set("sort_dir", sortDir || "asc");
    }

    const response = await fetch(`${PRODUCTS_API_BASE}?${params.toString()}`, {
        headers: {
            Accept: "application/json",
        },
    });

    await assertOk(response);

    return response.json();
}

export async function fetchProductById(productId) {
    const response = await fetch(`${PRODUCTS_API_BASE}/${productId}`, {
        headers: {
            Accept: "application/json",
        },
    });

    await assertOk(response);
    return response.json();
}

export async function createProduct(payload) {
    const response = await fetch(PRODUCTS_API_BASE, {
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

export async function updateProduct(productId, payload) {
    const response = await fetch(`${PRODUCTS_API_BASE}/${productId}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
        },
        body: JSON.stringify(payload),
    });

    await assertOk(response);
    return response.json();
}

export async function deleteProduct(productId) {
    const response = await fetch(`${PRODUCTS_API_BASE}/${productId}`, {
        method: "DELETE",
        headers: {
            Accept: "application/json",
        },
    });

    await assertOk(response);
}

export async function deactivateProduct(productId) {
    const response = await fetch(`${PRODUCTS_API_BASE}/${productId}/deactivate`, {
        method: "POST",
        headers: {
            Accept: "application/json",
        },
    });

    await assertOk(response);
    return response.json();
}

export async function activateProduct(productId) {
    const response = await fetch(`${PRODUCTS_API_BASE}/${productId}/activate`, {
        method: "POST",
        headers: {
            Accept: "application/json",
        },
    });

    await assertOk(response);
    return response.json();
}

export async function fetchCategories() {
    const response = await fetch(CATEGORIES_API_BASE, {
        headers: {
            Accept: "application/json",
        },
    });

    await assertOk(response);

    return response.json();
}
