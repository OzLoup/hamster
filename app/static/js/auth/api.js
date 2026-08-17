const AUTH_API_BASE = "/api/v1/auth";

export class ApiError extends Error {
    constructor(message, status) {
        super(message);
        this.name = "ApiError";
        this.status = status;
    }
}

function messageFromDetail(detail) {
    if (Array.isArray(detail)) {
        // FastAPI/Pydantic validation messages are always in English; show a
        // generic Spanish message instead of surfacing them untranslated.
        return "Revisa que el correo y la contraseña tengan un formato válido.";
    }
    if (typeof detail === "string" && detail.trim()) {
        return detail;
    }
    return "No se pudo iniciar sesión.";
}

async function assertOk(response) {
    if (response.ok) {
        return;
    }
    try {
        const payload = await response.json();
        throw new ApiError(messageFromDetail(payload.detail), response.status);
    } catch (error) {
        if (error instanceof ApiError) {
            throw error;
        }
        throw new ApiError("Request failed", response.status);
    }
}

export async function login({ email, password }) {
    const response = await fetch(`${AUTH_API_BASE}/login`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
        },
        body: JSON.stringify({ email, password }),
    });
    await assertOk(response);
    return response.json();
}

export async function logout() {
    const response = await fetch(`${AUTH_API_BASE}/logout`, {
        method: "POST",
        headers: { Accept: "application/json" },
    });
    await assertOk(response);
    return response.json();
}

export async function fetchCurrentUser() {
    const response = await fetch(`${AUTH_API_BASE}/me`, {
        headers: { Accept: "application/json" },
    });
    if (response.status === 401) {
        return null;
    }
    await assertOk(response);
    return response.json();
}
