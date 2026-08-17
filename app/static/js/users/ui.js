const ROLE_LABELS = {
    admin: "Administrador",
    coordinator: "Coordinador",
    seller: "Vendedor",
};

function initials(name) {
    const words = String(name || "Usuario").trim().split(/\s+/);
    return words.slice(0, 2).map((w) => w[0]?.toUpperCase() || "U").join("");
}

function renderEmptyState(tableBody) {
    tableBody.innerHTML = `
        <tr>
            <td colspan="5" class="px-3 py-8">
                <div class="saas-empty">No hay usuarios todavía. Crea el primero.</div>
            </td>
        </tr>
    `;
}

export function renderUsers(tableBody, users, currentUserId) {
    if (!users.length) {
        renderEmptyState(tableBody);
        return;
    }

    tableBody.innerHTML = users
        .map((user) => {
            const inactive = user.is_active === false;
            const toggleLabel = inactive ? "Activar" : "Desactivar";
            const isSelf = user.id === currentUserId;
            const roleLabel = ROLE_LABELS[user.role] || user.role || "—";

            return `
                <tr class="transition-colors hover:bg-slate-800/50 ${inactive ? "opacity-60" : ""}">
                    <td class="px-3 py-3">
                        <div class="flex items-center gap-3">
                            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500/25 to-cyan-500/20 text-xs font-semibold text-brand-200 ring-1 ring-brand-500/40">${initials(user.full_name)}</div>
                            <div>
                                <p class="font-medium text-slate-100">${user.full_name}${isSelf ? ' <span class="text-xs text-slate-500">(tú)</span>' : ""}</p>
                            </div>
                        </div>
                    </td>
                    <td class="px-3 py-3 text-slate-300">${user.email}</td>
                    <td class="px-3 py-3 text-slate-300">${roleLabel}</td>
                    <td class="px-3 py-3">
                        ${inactive
                            ? '<span class="inline-flex rounded-full bg-slate-700/60 px-2.5 py-1 text-xs font-medium text-slate-300 ring-1 ring-slate-600">Inactivo</span>'
                            : '<span class="inline-flex rounded-full bg-emerald-500/15 px-2.5 py-1 text-xs font-medium text-emerald-200 ring-1 ring-emerald-500/40">Activo</span>'}
                    </td>
                    <td class="px-3 py-3">
                        <div class="flex items-center justify-end gap-2">
                            <button data-action="edit" data-id="${user.id}" class="saas-btn saas-btn-primary rounded-lg px-2.5 py-1.5 text-xs">Editar</button>
                            <button
                                data-action="toggle-active"
                                data-id="${user.id}"
                                data-name="${user.full_name}"
                                data-active="${user.is_active}"
                                class="saas-btn saas-btn-muted rounded-lg px-2.5 py-1.5 text-xs disabled:cursor-not-allowed disabled:opacity-50"
                                ${isSelf ? "disabled" : ""}
                                title="${isSelf ? "No puedes desactivar tu propia cuenta" : ""}"
                            >${toggleLabel}</button>
                        </div>
                    </td>
                </tr>
            `;
        })
        .join("");
}

export function showError(errorBox, message) {
    errorBox.textContent = message;
    errorBox.classList.remove("hidden");
}

export function clearError(errorBox) {
    errorBox.textContent = "";
    errorBox.classList.add("hidden");
}
