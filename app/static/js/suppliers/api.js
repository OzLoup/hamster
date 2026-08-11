const SUPPLIERS_API_BASE = "/api/v1/suppliers";

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

export async function fetchSuppliers() {
    const response = await fetch(SUPPLIERS_API_BASE, {
        headers: {
            Accept: "application/json",
        },
    });

    await assertOk(response);
    return response.json();
}

export async function fetchSupplierById(supplierId) {
    const response = await fetch(`${SUPPLIERS_API_BASE}/${supplierId}`, {
        headers: {
            Accept: "application/json",
        },
    });

    await assertOk(response);
    return response.json();
}

export async function createSupplier(payload) {
    const response = await fetch(SUPPLIERS_API_BASE, {
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

export async function updateSupplier(supplierId, payload) {
    const response = await fetch(`${SUPPLIERS_API_BASE}/${supplierId}`, {
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

export async function deleteSupplier(supplierId) {
    const response = await fetch(`${SUPPLIERS_API_BASE}/${supplierId}`, {
        method: "DELETE",
        headers: {
            Accept: "application/json",
        },
    });

    await assertOk(response);
}

export async function deactivateSupplier(supplierId) {
    const response = await fetch(`${SUPPLIERS_API_BASE}/${supplierId}/deactivate`, {
        method: "POST",
        headers: {
            Accept: "application/json",
        },
    });

    await assertOk(response);
    return response.json();
}

export async function activateSupplier(supplierId) {
    const response = await fetch(`${SUPPLIERS_API_BASE}/${supplierId}/activate`, {
        method: "POST",
        headers: {
            Accept: "application/json",
        },
    });

    await assertOk(response);
    return response.json();
}
