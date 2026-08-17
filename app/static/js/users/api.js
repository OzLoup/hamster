const USERS_API_BASE = "/api/v1/users";

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

export async function fetchUsers() {
    const response = await fetch(USERS_API_BASE, { headers: { Accept: "application/json" } });
    await assertOk(response);
    return response.json();
}

export async function fetchUserById(userId) {
    const response = await fetch(`${USERS_API_BASE}/${userId}`, { headers: { Accept: "application/json" } });
    await assertOk(response);
    return response.json();
}

export async function createUser(payload) {
    const response = await fetch(USERS_API_BASE, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload),
    });
    await assertOk(response);
    return response.json();
}

export async function updateUser(userId, payload) {
    const response = await fetch(`${USERS_API_BASE}/${userId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload),
    });
    await assertOk(response);
    return response.json();
}

export async function deactivateUser(userId) {
    const response = await fetch(`${USERS_API_BASE}/${userId}/deactivate`, {
        method: "POST",
        headers: { Accept: "application/json" },
    });
    await assertOk(response);
    return response.json();
}

export async function activateUser(userId) {
    const response = await fetch(`${USERS_API_BASE}/${userId}/activate`, {
        method: "POST",
        headers: { Accept: "application/json" },
    });
    await assertOk(response);
    return response.json();
}
