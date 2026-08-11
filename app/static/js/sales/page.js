import { ApiError, fetchProductsForSale, submitSale } from "./api.js";
import { createSalesState } from "./state.js";
import { renderProductSearchOptions, renderSaleLines, renderSummary, setSubmitting, showMessage, clearMessage } from "./ui.js";
import { formatFastApiValidation, validateSaleInput } from "./validation.js";

const state = createSalesState();

const paymentSelect = document.getElementById("sale-payment");
const productSearchInput = document.getElementById("sale-product-search");
const productIdInput = document.getElementById("sale-product-id");
const productOptionsList = document.getElementById("sale-product-options");
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

let filteredProducts = [];
let activeOptionIndex = -1;

function normalize(text) {
    return text
        .toString()
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "");
}

function getFilteredProducts() {
    const query = normalize(productSearchInput?.value.trim() || "");
    if (!query) {
        return state.products;
    }
    return state.products.filter((product) => normalize(product.name).includes(query));
}

function renderOptionsList() {
    filteredProducts = getFilteredProducts();
    if (activeOptionIndex >= filteredProducts.length) {
        activeOptionIndex = filteredProducts.length - 1;
    }
    const activeId = filteredProducts[activeOptionIndex]?.id ?? null;
    renderProductSearchOptions(productOptionsList, filteredProducts, activeId);
}

function openProductOptions() {
    renderOptionsList();
    productOptionsList?.classList.remove("hidden");
    productSearchInput?.setAttribute("aria-expanded", "true");
}

function closeProductOptions() {
    productOptionsList?.classList.add("hidden");
    productSearchInput?.setAttribute("aria-expanded", "false");
    activeOptionIndex = -1;
}

function selectProduct(product) {
    if (!product || !productSearchInput || !productIdInput) {
        return;
    }
    productIdInput.value = String(product.id);
    productSearchInput.value = product.name;
    closeProductOptions();
}

function handleProductSearchInput() {
    const selected = state.productsById.get(Number(productIdInput?.value));
    if (!selected || selected.name !== productSearchInput?.value) {
        productIdInput.value = "";
    }
    activeOptionIndex = -1;
    openProductOptions();
}

function moveActiveOption(delta) {
    if (!filteredProducts.length) {
        return;
    }
    activeOptionIndex = (activeOptionIndex + delta + filteredProducts.length) % filteredProducts.length;
    renderOptionsList();
}

function handleProductSearchKeydown(event) {
    if (event.key === "ArrowDown") {
        event.preventDefault();
        if (productOptionsList?.classList.contains("hidden")) {
            openProductOptions();
            return;
        }
        moveActiveOption(1);
    } else if (event.key === "ArrowUp") {
        event.preventDefault();
        moveActiveOption(-1);
    } else if (event.key === "Enter") {
        event.preventDefault();
        const candidate = filteredProducts[activeOptionIndex] || filteredProducts[0];
        selectProduct(candidate);
    } else if (event.key === "Escape") {
        closeProductOptions();
    }
}

function handleProductOptionsClick(event) {
    const button = event.target.closest("button[data-id]");
    if (!button) {
        return;
    }
    selectProduct(state.productsById.get(Number(button.dataset.id)));
}

function handleOutsideProductClick(event) {
    if (!(event.target instanceof Node)) {
        return;
    }
    if (productSearchInput?.contains(event.target) || productOptionsList?.contains(event.target)) {
        return;
    }
    closeProductOptions();
}

function generateReference() {
    const payment = (paymentSelect?.value || "na").toUpperCase().slice(0, 3);
    const stamp = Date.now();
    return `SALE-${payment}-${stamp}`;
}

function addLine() {
    clearMessage(errorBox);
    clearMessage(successBox);

    const productId = Number(productIdInput?.value);
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

    const paymentMethod = paymentSelect?.value || "";
    const paymentMethodLabel = {
        cash: "efectivo",
        card: "tarjeta",
        nequi: "Nequi",
        daviplata: "Daviplata",
        bre_b: "Bre-B",
    }[paymentMethod] || paymentMethod.replace("_", " ");

    const validation = validateSaleInput({
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
        payment_method: paymentMethod,
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

        showMessage(successBox, `Venta registrada vía ${paymentMethodLabel}.`);
        notify("success", "Venta registrada correctamente.");
        state.lines = [];
        if (paymentSelect) {
            paymentSelect.value = "";
        }
        if (productSearchInput) {
            productSearchInput.value = "";
        }
        if (productIdInput) {
            productIdInput.value = "";
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
    } catch (error) {
        showMessage(errorBox, error.message || "No se pudieron cargar los productos para el registro de venta.");
        notify("error", error.message || "No se pudieron cargar los productos para el registro de venta.");
    }
}

function wireEvents() {
    addButton?.addEventListener("click", addLine);
    submitButton?.addEventListener("click", submitCurrentSale);
    tableBody?.addEventListener("click", handleLineActions);
    productSearchInput?.addEventListener("input", handleProductSearchInput);
    productSearchInput?.addEventListener("focus", openProductOptions);
    productSearchInput?.addEventListener("keydown", handleProductSearchKeydown);
    productOptionsList?.addEventListener("click", handleProductOptionsClick);
    document.addEventListener("click", handleOutsideProductClick);
}

wireEvents();
loadProducts();
refreshUI();
