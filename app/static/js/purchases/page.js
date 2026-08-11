import { ApiError, fetchActiveSuppliers, fetchProductsForPurchase, submitPurchase } from "./api.js";
import { createPurchasesState } from "./state.js";
import {
    clearMessage,
    renderPurchaseLines,
    renderProductSearchOptions,
    renderSummary,
    renderSupplierOptions,
    setSubmitting,
    showMessage,
} from "./ui.js";
import { formatFastApiValidation, validatePurchaseInput } from "./validation.js";

const state = createPurchasesState();

const supplierSelect = document.getElementById("purchase-supplier");
const productSearchInput = document.getElementById("purchase-product-search");
const productIdInput = document.getElementById("purchase-product-id");
const productOptionsList = document.getElementById("purchase-product-options");
const quantityInput = document.getElementById("purchase-quantity");
const unitCostInput = document.getElementById("purchase-unit-cost");
const addButton = document.getElementById("add-purchase-item");
const tableBody = document.getElementById("purchase-items-body");
const submitButton = document.getElementById("submit-purchase");
const submitSpinner = document.getElementById("purchase-submit-spinner");
const submitLabel = document.getElementById("purchase-submit-label");
const itemCountElement = document.getElementById("purchase-item-count");
const totalElement = document.getElementById("purchase-total");
const errorBox = document.getElementById("purchases-error");
const successBox = document.getElementById("purchases-success");

function notify(type, message, duration = 3200) {
    window.showToast?.({ type, message, duration });
}

function getRunningTotal() {
    return state.lines.reduce((acc, line) => acc + line.subtotal, 0);
}

function refreshUI() {
    renderPurchaseLines(tableBody, state.lines);
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
    const supplierId = supplierSelect?.value || "0";
    const stamp = Date.now();
    return `PUR-${supplierId}-${stamp}`;
}

function addLine() {
    clearMessage(errorBox);
    clearMessage(successBox);

    const productId = Number(productIdInput?.value);
    const quantity = Number(quantityInput?.value || 0);
    const unitCost = Number(unitCostInput?.value);

    if (!productId) {
        showMessage(errorBox, "Por favor selecciona un producto.");
        notify("warning", "Selecciona un producto antes de agregar una línea de compra.");
        return;
    }

    if (!Number.isInteger(quantity) || quantity <= 0) {
        showMessage(errorBox, "La cantidad debe ser un número entero positivo.");
        notify("warning", "La cantidad debe ser un número entero positivo.");
        return;
    }

    if (!Number.isFinite(unitCost) || unitCost < 0) {
        showMessage(errorBox, "El costo unitario debe ser un número válido.");
        notify("warning", "El costo unitario debe ser un número válido.");
        return;
    }

    const product = state.productsById.get(productId);
    if (!product) {
        showMessage(errorBox, "El producto seleccionado no está disponible.");
        notify("error", "El producto seleccionado no está disponible.");
        return;
    }

    const roundedUnitCost = Number(unitCost.toFixed(2));
    const existing = state.lines.find((line) => line.productId === productId);
    const nextQuantity = (existing?.quantity || 0) + quantity;

    if (existing) {
        existing.quantity = nextQuantity;
        existing.unitCost = roundedUnitCost;
        existing.subtotal = Number((roundedUnitCost * nextQuantity).toFixed(2));
    } else {
        state.lines.push({
            productId,
            name: product.name,
            unitCost: roundedUnitCost,
            quantity,
            subtotal: Number((roundedUnitCost * quantity).toFixed(2)),
        });
    }

    quantityInput.value = "1";
    unitCostInput.value = "";
    refreshUI();
}

function removeLine(productId) {
    state.lines = state.lines.filter((line) => line.productId !== productId);
    refreshUI();
}

async function submitCurrentPurchase() {
    clearMessage(errorBox);
    clearMessage(successBox);

    const supplierId = Number(supplierSelect?.value) || null;

    const validation = validatePurchaseInput({
        supplierId,
        lines: state.lines,
    });

    if (!validation.isValid) {
        showMessage(errorBox, validation.errors.join(" "));
        notify("warning", "Por favor completa los datos requeridos de la compra antes de enviar.");
        return;
    }

    const total = Number(getRunningTotal().toFixed(2));

    const payload = {
        reference: generateReference(),
        supplier_id: supplierId,
        total_amount: total.toFixed(2),
        purchase_items: state.lines.map((line) => ({
            product_id: line.productId,
            quantity: line.quantity,
            unit_cost: line.unitCost.toFixed(2),
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

        await submitPurchase(payload);

        showMessage(successBox, "Compra registrada correctamente. El stock y el costo de los productos ya se actualizaron.");
        notify("success", "Compra registrada correctamente.");
        state.lines = [];
        if (supplierSelect) {
            supplierSelect.value = "";
        }
        if (productSearchInput) {
            productSearchInput.value = "";
        }
        if (productIdInput) {
            productIdInput.value = "";
        }
        refreshUI();

        // Refresh products to keep stock and cost display in sync after successful purchase.
        await loadProducts();
    } catch (error) {
        if (error instanceof ApiError) {
            const details = formatFastApiValidation(error.details);
            showMessage(errorBox, details.length ? details.join(" ") : error.message);
            notify("error", details.length ? "Error de validación al enviar la compra." : error.message);
            return;
        }
        showMessage(errorBox, error.message || "No se pudo registrar la compra.");
        notify("error", error.message || "No se pudo registrar la compra.");
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
        const products = await fetchProductsForPurchase();
        state.products = products;
        state.productsById = new Map(products.map((product) => [product.id, product]));
    } catch (error) {
        showMessage(errorBox, error.message || "No se pudieron cargar los productos para el registro de compra.");
        notify("error", error.message || "No se pudieron cargar los productos para el registro de compra.");
    }
}

async function loadSuppliers() {
    try {
        const suppliers = await fetchActiveSuppliers();
        state.suppliers = suppliers;
        renderSupplierOptions(supplierSelect, suppliers);
    } catch (error) {
        showMessage(errorBox, error.message || "No se pudieron cargar los proveedores.");
        notify("error", error.message || "No se pudieron cargar los proveedores.");
    }
}

function wireEvents() {
    addButton?.addEventListener("click", addLine);
    submitButton?.addEventListener("click", submitCurrentPurchase);
    tableBody?.addEventListener("click", handleLineActions);
    productSearchInput?.addEventListener("input", handleProductSearchInput);
    productSearchInput?.addEventListener("focus", openProductOptions);
    productSearchInput?.addEventListener("keydown", handleProductSearchKeydown);
    productOptionsList?.addEventListener("click", handleProductOptionsClick);
    document.addEventListener("click", handleOutsideProductClick);
}

wireEvents();
loadSuppliers();
loadProducts();
refreshUI();
