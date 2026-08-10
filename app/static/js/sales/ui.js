function currency(value) {
    const amount = Number(value);
    if (Number.isNaN(amount)) {
        return "$0.00";
    }
    return new Intl.NumberFormat("es-419", {
        style: "currency",
        currency: "USD",
    }).format(amount);
}

export function renderProductOptions(selectElement, products) {
    if (!selectElement) {
        return;
    }

    selectElement.innerHTML = [
        '<option value="">Selecciona un producto</option>',
        ...products.map(
            (product) =>
                `<option value="${product.id}">${product.name} (Stock disponible: ${product.stock_quantity})</option>`
        ),
    ].join("");
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
