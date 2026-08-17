const BUSINESSES_API_BASE = "/api/v1/admin/businesses";
const SUPERUSERS_API_BASE = "/api/v1/admin/superusers";

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
            return { message: "Validación fallida.", details: detail };
        }
        if (typeof detail === "string" && detail.trim()) {
            return { message: detail, details: null };
        }
        return { message: "Error en la solicitud", details: null };
    } catch {
        return { message: "Error en la solicitud", details: null };
    }
}

async function assertOk(response) {
    if (response.ok) {
        return;
    }
    const parsed = await parseError(response);
    throw new ApiError(parsed.message, response.status, parsed.details);
}

export async function fetchBusinesses() {
    const response = await fetch(BUSINESSES_API_BASE, { headers: { Accept: "application/json" } });
    await assertOk(response);
    return response.json();
}

export async function createBusiness(payload) {
    const response = await fetch(BUSINESSES_API_BASE, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload),
    });
    await assertOk(response);
    return response.json();
}

export async function deactivateBusiness(businessId) {
    const response = await fetch(`${BUSINESSES_API_BASE}/${businessId}/deactivate`, {
        method: "POST",
        headers: { Accept: "application/json" },
    });
    await assertOk(response);
    return response.json();
}

export async function activateBusiness(businessId) {
    const response = await fetch(`${BUSINESSES_API_BASE}/${businessId}/activate`, {
        method: "POST",
        headers: { Accept: "application/json" },
    });
    await assertOk(response);
    return response.json();
}

export async function fetchSuperusers() {
    const response = await fetch(SUPERUSERS_API_BASE, { headers: { Accept: "application/json" } });
    await assertOk(response);
    return response.json();
}

export async function createSuperuser(payload) {
    const response = await fetch(SUPERUSERS_API_BASE, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload),
    });
    await assertOk(response);
    return response.json();
}

export async function deactivateSuperuser(userId) {
    const response = await fetch(`${SUPERUSERS_API_BASE}/${userId}/deactivate`, {
        method: "POST",
        headers: { Accept: "application/json" },
    });
    await assertOk(response);
    return response.json();
}

export async function activateSuperuser(userId) {
    const response = await fetch(`${SUPERUSERS_API_BASE}/${userId}/activate`, {
        method: "POST",
        headers: { Accept: "application/json" },
    });
    await assertOk(response);
    return response.json();
}
