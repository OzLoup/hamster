function currency(value) {
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

export function renderSaleLines(tableBody, lines) {
    if (!tableBody) {
        return;
    }

    if (!lines.length) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="px-3 py-8">
                    <div class="saas-empty">Aún no hay productos agregados.</div>
                </td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = lines
        .map(
            (line) => `
                <tr class="transition-colors hover:bg-slate-800/40">
                    <td class="px-3 py-3 text-slate-100">${line.name}</td>
                    <td class="px-3 py-3 text-slate-200">${currency(line.unitPrice)}</td>
                    <td class="px-3 py-3 text-slate-200">${line.quantity}</td>
                    <td class="px-3 py-3 text-slate-200">${currency(line.subtotal)}</td>
                    <td class="px-3 py-3">
                        <div class="flex justify-end">
                            <button data-action="remove" data-id="${line.productId}" class="saas-btn saas-btn-danger rounded-lg px-2.5 py-1.5 text-xs">Eliminar</button>
                        </div>
                    </td>
                </tr>
            `
        )
        .join("");
}

export function renderSummary({ lines, total, itemCountElement, totalElement }) {
    if (itemCountElement) {
        itemCountElement.textContent = String(lines.length);
    }
    if (totalElement) {
        totalElement.textContent = currency(total);
    }
}

export function setSubmitting({ submitButton, spinner, label, isSubmitting }) {
    if (submitButton) {
        submitButton.disabled = isSubmitting;
    }
    if (spinner) {
        spinner.classList.toggle("hidden", !isSubmitting);
    }
    if (label) {
        label.textContent = isSubmitting ? "Enviando..." : "Enviar venta";
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
