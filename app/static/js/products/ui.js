function currency(value) {
    const amount = Number(value);
    if (Number.isNaN(amount)) {
        return "$0.00";
    }
    return new Intl.NumberFormat("es-419", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 2,
    }).format(amount);
}


function stockStatus(stock) {
    if (stock <= 10) {
        return {
            label: "Bajo",
            className: "bg-rose-500/15 text-rose-200 ring-1 ring-rose-500/40",
        };
    }
    if (stock <= 30) {
        return {
            label: "Medio",
            className: "bg-amber-500/15 text-amber-200 ring-1 ring-amber-500/40",
        };
    }
    return {
        label: "En stock",
        className: "bg-emerald-500/15 text-emerald-200 ring-1 ring-emerald-500/40",
    };
}

function initials(name) {
    const words = String(name || "Producto").trim().split(/\s+/);
    return words.slice(0, 2).map((w) => w[0]?.toUpperCase() || "P").join("");
}

function renderEmptyState(tableBody) {
    tableBody.innerHTML = `
        <tr>
            <td colspan="7" class="px-3 py-8">
                <div class="saas-empty">
                    <div class="mx-auto inline-flex h-10 w-10 items-center justify-center rounded-xl border border-teal-500/40 bg-teal-500/10 text-teal-200">
                        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75L12 3l8.25 3.75M3.75 6.75V17.25L12 21m-8.25-14.25L12 10.5m8.25-3.75V17.25L12 21m0-10.5V21"/>
                        </svg>
                    </div>
                    <p class="mt-3 font-medium text-slate-200">No se encontraron productos</p>
                    <p class="mt-1 text-sm text-slate-400">Prueba otro término de búsqueda o crea un producto nuevo.</p>
                </div>
            </td>
        </tr>
    `;
}

export function renderProducts(tableBody, products, categoriesById) {
    if (!products.length) {
        renderEmptyState(tableBody);
        return;
    }

    tableBody.innerHTML = products
        .map((product) => {
            const status = stockStatus(product.stock_quantity);
            const categoryName = categoriesById.get(product.category_id) || `Categoría #${product.category_id}`;

            return `
                <tr class="transition-colors hover:bg-slate-800/50">
                    <td class="px-3 py-3">
                        <div class="flex items-center gap-3">
                            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500/25 to-cyan-500/20 text-xs font-semibold text-brand-200 ring-1 ring-brand-500/40">${initials(product.name)}</div>
                            <div>
                                <p class="font-medium text-slate-100">${product.name}</p>
                                <p class="text-xs text-slate-400">SKU: ${product.sku}</p>
                            </div>
                        </div>
                    </td>
                    <td class="px-3 py-3 text-slate-300">${categoryName}</td>
                    <td class="px-3 py-3 text-slate-200">${product.stock_quantity}</td>
                    <td class="px-3 py-3 text-slate-200">${currency(product.cost)}</td>
                    <td class="px-3 py-3 text-slate-200">${currency(product.sale_price)}</td>
                    <td class="px-3 py-3">
                        <span class="inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${status.className}">${status.label}</span>
                    </td>
                    <td class="px-3 py-3">
                        <div class="flex items-center justify-end gap-2">
                            <button data-action="view" data-id="${product.id}" class="saas-btn saas-btn-muted rounded-lg px-2.5 py-1.5 text-xs">Ver</button>
                            <button data-action="edit" data-id="${product.id}" class="saas-btn saas-btn-primary rounded-lg px-2.5 py-1.5 text-xs">Editar</button>
                            <button data-action="delete" data-id="${product.id}" class="saas-btn saas-btn-danger rounded-lg px-2.5 py-1.5 text-xs">Eliminar</button>
                        </div>
                    </td>
                </tr>
            `;
        })
        .join("");
}

export function renderPagination({ state, count, prevButton, nextButton, pageIndicator, meta }) {
    const start = count === 0 ? 0 : (state.page - 1) * state.pageSize + 1;
    const end = count === 0 ? 0 : start + count - 1;

meta.textContent = `Mostrando ${start} a ${end} de ${state.total} productos`;
    pageIndicator.textContent = `Página ${state.page} de ${state.totalPages}`;

    prevButton.disabled = state.page <= 1;
    nextButton.disabled = state.page >= state.totalPages;
}

export function showError(errorBox, message) {
    errorBox.textContent = message;
    errorBox.classList.remove("hidden");
}

export function clearError(errorBox) {
    errorBox.textContent = "";
    errorBox.classList.add("hidden");
}
