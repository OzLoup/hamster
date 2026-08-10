function initials(name) {
    const words = String(name || "Categoría").trim().split(/\s+/);
    return words.slice(0, 2).map((w) => w[0]?.toUpperCase() || "C").join("");
}

function formatDate(value) {
    if (!value) {
        return "-";
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return "-";
    }

    return new Intl.DateTimeFormat("es-419", {
        year: "numeric",
        month: "short",
        day: "2-digit",
    }).format(date);
}

function renderEmptyState(tableBody) {
    tableBody.innerHTML = `
        <tr>
            <td colspan="4" class="px-3 py-8">
                <div class="saas-empty">
                    <div class="mx-auto inline-flex h-10 w-10 items-center justify-center rounded-xl border border-brand-500/40 bg-brand-500/10 text-brand-200">
                        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 5.25h6.75v6.75H3.75V5.25zm9.75 0h6.75v6.75H13.5V5.25zM3.75 14.25h6.75V21H3.75v-6.75zm9.75 0h6.75V21H13.5v-6.75z"/>
                        </svg>
                    </div>
                    <p class="mt-3 font-medium text-slate-200">No se encontraron categorías</p>
                    <p class="mt-1 text-sm text-slate-400">Ajusta los filtros o agrega una nueva categoría.</p>
                </div>
            </td>
        </tr>
    `;
}

export function renderCategories(tableBody, categories) {
    if (!categories.length) {
        renderEmptyState(tableBody);
        return;
    }

    tableBody.innerHTML = categories
        .map((category) => {
            const description = category.description || "Sin descripción";
            return `
                <tr class="transition-colors hover:bg-slate-800/50">
                    <td class="px-3 py-3">
                        <div class="flex items-center gap-3">
                            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500/25 to-cyan-500/20 text-xs font-semibold text-brand-200 ring-1 ring-brand-500/40">${initials(category.name)}</div>
                            <p class="font-medium text-slate-100">${category.name}</p>
                        </div>
                    </td>
                    <td class="px-3 py-3 text-slate-300">${description}</td>
                    <td class="px-3 py-3 text-slate-300">${formatDate(category.created_at)}</td>
                    <td class="px-3 py-3">
                        <div class="flex items-center justify-end gap-2">
                            <button data-action="edit" data-id="${category.id}" class="saas-btn saas-btn-primary rounded-lg px-2.5 py-1.5 text-xs">Editar</button>
                            <button data-action="delete" data-id="${category.id}" data-name="${category.name}" class="saas-btn saas-btn-danger rounded-lg px-2.5 py-1.5 text-xs">Eliminar</button>
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
