const SETTINGS_API_BASE = "/api/v1/settings";

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

export async function fetchSettings() {
    const response = await fetch(SETTINGS_API_BASE, {
        headers: {
            Accept: "application/json",
        },
    });

    await assertOk(response);
    return response.json();
}

export async function updateSettings(payload) {
    const response = await fetch(SETTINGS_API_BASE, {
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
