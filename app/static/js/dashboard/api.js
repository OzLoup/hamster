const DASHBOARD_API_BASE = "/api/v1/dashboard";

export class ApiError extends Error {
    constructor(message, status) {
        super(message);
        this.name = "ApiError";
        this.status = status;
    }
}

async function parseError(response) {
    try {
        const payload = await response.json();
        const detail = payload.detail;
        if (typeof detail === "string" && detail.trim()) {
            return { message: detail };
        }
        return { message: "Error en la solicitud" };
    } catch {
        return { message: "Error en la solicitud" };
    }
}

async function assertOk(response) {
    if (response.ok) {
        return;
    }
    const parsed = await parseError(response);
    throw new ApiError(parsed.message, response.status);
}

export async function fetchDashboardSummary() {
    const params = new URLSearchParams();
    const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (timeZone) {
        params.set("tz", timeZone);
    }

    const response = await fetch(`${DASHBOARD_API_BASE}/summary?${params.toString()}`, {
        headers: {
            Accept: "application/json",
        },
    });

    await assertOk(response);
    return response.json();
}

export async function fetchLowStockProducts() {
    const response = await fetch(`${DASHBOARD_API_BASE}/low-stock-products`, {
        headers: {
            Accept: "application/json",
        },
    });

    await assertOk(response);
    return response.json();
}
