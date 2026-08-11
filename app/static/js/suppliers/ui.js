function initials(name) {
    const words = String(name || "Proveedor").trim().split(/\s+/);
    return words.slice(0, 2).map((w) => w[0]?.toUpperCase() || "P").join("");
}

function renderEmptyState(tableBody) {
    tableBody.innerHTML = `
        <tr>
            <td colspan="5" class="px-3 py-8">
                <div class="saas-empty">
                    <div class="mx-auto inline-flex h-10 w-10 items-center justify-center rounded-xl border border-brand-500/40 bg-brand-500/10 text-brand-200">
                        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25M21 7.5v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9"/>
                        </svg>
                    </div>
                    <p class="mt-3 font-medium text-slate-200">No se encontraron proveedores</p>
                    <p class="mt-1 text-sm text-slate-400">Ajusta los filtros o agrega un nuevo proveedor.</p>
                </div>
            </td>
        </tr>
    `;
}

export function renderSuppliers(tableBody, suppliers) {
    if (!suppliers.length) {
        renderEmptyState(tableBody);
        return;
    }

    tableBody.innerHTML = suppliers
        .map((supplier) => {
            const inactive = supplier.is_active === false;
            const toggleLabel = inactive ? "Activar" : "Desactivar";
            const contact = supplier.contact_name || "Sin contacto";
            const reach = [supplier.phone, supplier.email].filter(Boolean).join(" · ") || "Sin datos de contacto";

            return `
                <tr class="transition-colors hover:bg-slate-800/50 ${inactive ? "opacity-60" : ""}">
                    <td class="px-3 py-3">
                        <div class="flex items-center gap-3">
                            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500/25 to-cyan-500/20 text-xs font-semibold text-brand-200 ring-1 ring-brand-500/40">${initials(supplier.name)}</div>
                            <p class="font-medium text-slate-100">${supplier.name}</p>
                        </div>
                    </td>
                    <td class="px-3 py-3 text-slate-300">${contact}</td>
                    <td class="px-3 py-3 text-slate-300">${reach}</td>
                    <td class="px-3 py-3">
                        ${inactive
                            ? '<span class="inline-flex rounded-full bg-slate-700/60 px-2.5 py-1 text-xs font-medium text-slate-300 ring-1 ring-slate-600">Inactivo</span>'
                            : '<span class="inline-flex rounded-full bg-emerald-500/15 px-2.5 py-1 text-xs font-medium text-emerald-200 ring-1 ring-emerald-500/40">Activo</span>'}
                    </td>
                    <td class="px-3 py-3">
                        <div class="flex items-center justify-end gap-2">
                            <button data-action="edit" data-id="${supplier.id}" class="saas-btn saas-btn-primary rounded-lg px-2.5 py-1.5 text-xs">Editar</button>
                            <button data-action="toggle-active" data-id="${supplier.id}" data-name="${supplier.name}" data-active="${supplier.is_active}" class="saas-btn saas-btn-muted rounded-lg px-2.5 py-1.5 text-xs">${toggleLabel}</button>
                            <button data-action="delete" data-id="${supplier.id}" data-name="${supplier.name}" class="saas-btn saas-btn-danger rounded-lg px-2.5 py-1.5 text-xs">Eliminar</button>
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
