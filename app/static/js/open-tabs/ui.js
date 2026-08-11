export function currency(value) {
    const amount = Number(value);
    if (Number.isNaN(amount)) {
        return "$ 0";
    }
    return new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP",
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    }).format(amount);
}

export function renderTabsGrid(container, tabs) {
    if (!container) {
        return;
    }

    if (!tabs.length) {
        container.innerHTML = `
            <div class="saas-card col-span-full rounded-3xl p-8 text-center">
                <div class="saas-empty">Aún no tienes cuentas abiertas. Crea una para empezar (una mesa, un cliente fiado, un mostrador...).</div>
            </div>
        `;
        return;
    }

    container.innerHTML = tabs
        .map((tab) => {
            const itemCount = tab.items.length;
            const hasItems = itemCount > 0;
            return `
                <article class="saas-card flex flex-col justify-between rounded-3xl p-5 sm:p-6" data-tab-card="${tab.id}">
                    <div>
                        <div class="flex items-start justify-between gap-3">
                            <h3 class="truncate text-base font-semibold text-slate-100">${tab.name}</h3>
                            <button
                                data-action="delete"
                                data-id="${tab.id}"
                                type="button"
                                class="shrink-0 rounded-lg p-1.5 text-slate-400 transition hover:bg-rose-500/10 hover:text-rose-300"
                                aria-label="Eliminar cuenta"
                            >
                                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 7.5h12M9.75 7.5V5.25a1.5 1.5 0 0 1 1.5-1.5h1.5a1.5 1.5 0 0 1 1.5 1.5V7.5m-7.5 0v12a1.5 1.5 0 0 0 1.5 1.5h6a1.5 1.5 0 0 0 1.5-1.5v-12"/>
                                </svg>
                            </button>
                        </div>
                        <p class="mt-1 text-xs text-slate-400">${hasItems ? `${itemCount} producto${itemCount === 1 ? "" : "s"} sin cobrar` : "Sin productos por ahora"}</p>
                    </div>
                    <div class="mt-5 flex items-center justify-between">
                        <span class="text-lg font-semibold ${hasItems ? "text-emerald-300" : "text-slate-500"}">${currency(tab.total)}</span>
                        <button data-action="manage" data-id="${tab.id}" type="button" class="saas-btn saas-btn-primary px-3.5 py-2 text-xs">Gestionar</button>
                    </div>
                </article>
            `;
        })
        .join("");
}

export function renderProductSearchOptions(container, products, activeId = null) {
    if (!container) {
        return;
    }

    if (!products.length) {
        container.innerHTML = '<p class="px-3 py-3 text-sm text-slate-400">No se encontraron productos.</p>';
        return;
    }

    container.innerHTML = products
        .map((product) => {
            const isActive = product.id === activeId;
            const outOfStock = product.stock_quantity <= 0;
            return `
                <button
                    type="button"
                    role="option"
                    data-id="${product.id}"
                    aria-selected="${isActive}"
                    class="flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm transition-colors ${isActive ? "bg-slate-800 text-white" : "text-slate-200 hover:bg-slate-800/70"}"
                >
                    <span class="truncate">${product.name}</span>
                    <span class="shrink-0 text-xs ${outOfStock ? "text-rose-300" : "text-slate-400"}">${outOfStock ? "Sin stock" : `Stock: ${product.stock_quantity}`}</span>
                </button>
            `;
        })
        .join("");
}

export function renderTabItems(tableBody, items) {
    if (!tableBody) {
        return;
    }

    if (!items.length) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="px-3 py-8">
                    <div class="saas-empty">Aún no hay productos en esta cuenta.</div>
                </td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = items
        .map(
            (item) => `
                <tr class="transition-colors hover:bg-slate-800/40">
                    <td class="px-3 py-3 text-slate-100">${item.product_name}</td>
                    <td class="px-3 py-3 text-slate-200">${currency(item.unit_price)}</td>
                    <td class="px-3 py-3 text-slate-200">${item.quantity}</td>
                    <td class="px-3 py-3 text-slate-200">${currency(item.subtotal)}</td>
                    <td class="px-3 py-3">
                        <div class="flex justify-end">
                            <button data-action="remove-item" data-id="${item.id}" class="saas-btn saas-btn-danger rounded-lg px-2.5 py-1.5 text-xs">Quitar</button>
                        </div>
                    </td>
                </tr>
            `
        )
        .join("");
}

export function renderTabTotal(element, total) {
    if (element) {
        element.textContent = currency(total);
    }
}

export function setSubmitting({ button, spinner, label, isSubmitting, submittingText, idleText }) {
    if (button) {
        button.disabled = isSubmitting;
    }
    if (spinner) {
        spinner.classList.toggle("hidden", !isSubmitting);
    }
    if (label) {
        label.textContent = isSubmitting ? submittingText : idleText;
    }
}

export function showMessage(element, message) {
    if (!element) {
        return;
    }
    element.textContent = message;
    element.classList.remove("hidden");
}

export function clearMessage(element) {
    if (!element) {
        return;
    }
    element.textContent = "";
    element.classList.add("hidden");
}
