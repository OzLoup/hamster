import { ApiError, fetchProductsForSale, submitSale } from "./api.js";
import { createSalesState } from "./state.js";
import { renderProductOptions, renderSaleLines, renderSummary, setSubmitting, showMessage, clearMessage } from "./ui.js";
import { formatFastApiValidation, validateSaleInput } from "./validation.js";

const state = createSalesState();

const customerInput = document.getElementById("sale-customer");
const paymentSelect = document.getElementById("sale-payment");
const productSelect = document.getElementById("sale-product-select");
const quantityInput = document.getElementById("sale-quantity");
const addButton = document.getElementById("add-sale-item");
const tableBody = document.getElementById("sale-items-body");
const submitButton = document.getElementById("submit-sale");
const submitSpinner = document.getElementById("sale-submit-spinner");
const submitLabel = document.getElementById("sale-submit-label");
const itemCountElement = document.getElementById("sale-item-count");
const totalElement = document.getElementById("sale-total");
const errorBox = document.getElementById("sales-error");
const successBox = document.getElementById("sales-success");

function notify(type, message, duration = 3200) {
    window.showToast?.({ type, message, duration });
}

function getRunningTotal() {
    return state.lines.reduce((acc, line) => acc + line.subtotal, 0);
}

function refreshUI() {
    renderSaleLines(tableBody, state.lines);
    renderSummary({
        lines: state.lines,
        total: getRunningTotal(),
        itemCountElement,
        totalElement,
    });
}

function generateReference() {
    const customer = (customerInput?.value || "customer").trim().toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 8) || "CUST";
    const payment = (paymentSelect?.value || "na").toUpperCase().slice(0, 3);
    const stamp = Date.now();
    return `SALE-${payment}-${customer}-${stamp}`;
}

function addLine() {
    clearMessage(errorBox);
    clearMessage(successBox);

    const productId = Number(productSelect?.value);
    const quantity = Number(quantityInput?.value || 0);

    if (!productId) {
        showMessage(errorBox, "Por favor selecciona un producto.");
        notify("warning", "Selecciona un producto antes de agregar una línea de venta.");
        return;
    }

    if (!Number.isInteger(quantity) || quantity <= 0) {
        showMessage(errorBox, "La cantidad debe ser un número entero positivo.");
        notify("warning", "La cantidad debe ser un número entero positivo.");
        return;
    }

    const product = state.productsById.get(productId);
    if (!product) {
        showMessage(errorBox, "El producto seleccionado no está disponible.");
        notify("error", "El producto seleccionado no está disponible.");
        return;
    }

    const existing = state.lines.find((line) => line.productId === productId);
    const nextQuantity = (existing?.quantity || 0) + quantity;
    if (nextQuantity > product.stock_quantity) {
        showMessage(errorBox, `La cantidad supera el stock disponible (${product.stock_quantity}).`);
        notify("warning", `La cantidad supera el stock disponible (${product.stock_quantity}).`);
        return;
    }

    const unitPrice = Number(product.sale_price);
    const subtotal = Number((unitPrice * nextQuantity).toFixed(2));

    if (existing) {
        existing.quantity = nextQuantity;
        existing.subtotal = subtotal;
    } else {
        state.lines.push({
            productId,
            name: product.name,
            unitPrice,
            quantity,
            subtotal: Number((unitPrice * quantity).toFixed(2)),
        });
    }

    quantityInput.value = "1";
    refreshUI();
}

function removeLine(productId) {
    state.lines = state.lines.filter((line) => line.productId !== productId);
    refreshUI();
}

async function submitCurrentSale() {
    clearMessage(errorBox);
    clearMessage(successBox);

    const customerName = (customerInput?.value || "").trim();
    const paymentMethod = paymentSelect?.value || "";
    const paymentMethodLabel = {
        cash: "efectivo",
        card: "tarjeta",
        bank_transfer: "transferencia bancaria",
        digital_wallet: "billetera digital",
    }[paymentMethod] || paymentMethod.replace("_", " ");

    const validation = validateSaleInput({
        customerName,
        paymentMethod,
        lines: state.lines,
    });

    if (!validation.isValid) {
        showMessage(errorBox, validation.errors.join(" "));
        notify("warning", "Por favor completa los datos requeridos de la venta antes de enviar.");
        return;
    }

    const total = Number(getRunningTotal().toFixed(2));

    const payload = {
        reference: generateReference(),
        total_amount: total.toFixed(2),
        sale_items: state.lines.map((line) => ({
            product_id: line.productId,
            quantity: line.quantity,
            unit_price: line.unitPrice.toFixed(2),
            subtotal: line.subtotal.toFixed(2),
        })),
    };

    try {
        setSubmitting({
            submitButton,
            spinner: submitSpinner,
            label: submitLabel,
            isSubmitting: true,
        });

        await submitSale(payload);

        showMessage(successBox, `Venta registrada para ${customerName} vía ${paymentMethodLabel}.`);
        notify("success", "Venta registrada correctamente.");
        state.lines = [];
        if (customerInput) {
            customerInput.value = "";
        }
        if (paymentSelect) {
            paymentSelect.value = "";
        }
        refreshUI();

        // Refresh products to keep stock display in sync after successful sale.
        await loadProducts();
    } catch (error) {
        if (error instanceof ApiError) {
            const details = formatFastApiValidation(error.details);
            showMessage(errorBox, details.length ? details.join(" ") : error.message);
            notify("error", details.length ? "Error de validación al enviar la venta." : error.message);
            return;
        }
        showMessage(errorBox, error.message || "No se pudo registrar la venta.");
        notify("error", error.message || "No se pudo registrar la venta.");
    } finally {
        setSubmitting({
            submitButton,
            spinner: submitSpinner,
            label: submitLabel,
            isSubmitting: false,
        });
    }
}

function handleLineActions(event) {
    const target = event.target;
    if (!(target instanceof HTMLElement)) {
        return;
    }

    const button = target.closest("button[data-action='remove']");
    if (!button) {
        return;
    }

    const productId = Number(button.dataset.id);
    removeLine(productId);
}

async function loadProducts() {
    try {
        const products = await fetchProductsForSale();
        state.products = products;
        state.productsById = new Map(products.map((product) => [product.id, product]));
        renderProductOptions(productSelect, products);
    } catch (error) {
        showMessage(errorBox, error.message || "No se pudieron cargar los productos para el registro de venta.");
        notify("error", error.message || "No se pudieron cargar los productos para el registro de venta.");
    }
}

function wireEvents() {
    addButton?.addEventListener("click", addLine);
    submitButton?.addEventListener("click", submitCurrentSale);
    tableBody?.addEventListener("click", handleLineActions);
}

wireEvents();
loadProducts();
refreshUI();
