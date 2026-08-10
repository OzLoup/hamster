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

export async function fetchCategories() {
    const response = await fetch(CATEGORIES_API_BASE, {
        headers: {
            Accept: "application/json",
        },
    });

    await assertOk(response);
    return response.json();
}

export async function fetchCategoryById(categoryId) {
    const response = await fetch(`${CATEGORIES_API_BASE}/${categoryId}`, {
        headers: {
            Accept: "application/json",
        },
    });

    await assertOk(response);
    return response.json();
}

export async function createCategory(payload) {
    const response = await fetch(CATEGORIES_API_BASE, {
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

export async function updateCategory(categoryId, payload) {
    const response = await fetch(`${CATEGORIES_API_BASE}/${categoryId}`, {
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

export async function deleteCategory(categoryId) {
    const response = await fetch(`${CATEGORIES_API_BASE}/${categoryId}`, {
        method: "DELETE",
        headers: {
            Accept: "application/json",
        },
    });

    await assertOk(response);
}
