import {
    ApiError,
    createProduct,
    fetchActiveSuppliers,
    fetchCategories,
    fetchProductsForPurchase,
    submitPurchase,
} from "./api.js";
import { createPurchasesState } from "./state.js";
import {
    clearMessage,
    renderCategoryOptions,
    renderPurchaseLines,
    renderProductSearchOptions,
    renderSummary,
    renderSupplierOptions,
    setSubmitting,
    showMessage,
} from "./ui.js";
import { formatFastApiValidation, validateNewProductPayload, validatePurchaseInput } from "./validation.js";

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

const newProductButton = document.getElementById("open-new-product-modal");
const newProductOverlay = document.getElementById("new-product-modal-overlay");
const newProductPanel = document.getElementById("new-product-modal-panel");
const closeNewProductButton = document.getElementById("close-new-product-modal");
const cancelNewProductButton = document.getElementById("cancel-new-product-modal");
const newProductForm = document.getElementById("new-product-form");
const newProductErrorBox = document.getElementById("new-product-modal-errors");
const newProductSubmitButton = document.getElementById("submit-new-product");
const newProductSubmitSpinner = document.getElementById("new-product-submit-spinner");
const newProductNameInput = document.getElementById("new-product-name");
const newProductCategorySelect = document.getElementById("new-product-category");
const newProductCostInput = document.getElementById("new-product-cost");
const newProductSalePriceInput = document.getElementById("new-product-sale-price");
const newProductFieldInputs = Array.from(document.querySelectorAll(".new-product-field"));

let categoriesLoaded = false;

function notify(type, message, duration = 3200) {
    window.showToast?.({ type, message, duration });
}

function fieldErrorClass(input) {
    input.classList.add("border-rose-500", "ring-rose-500/40");
    input.classList.remove("border-slate-700", "focus:border-brand-400", "focus:ring-brand-500/40");
}

function clearFieldErrorClass(input) {
    input.classList.remove("border-rose-500", "ring-rose-500/40");
    input.classList.add("border-slate-700", "focus:border-brand-400", "focus:ring-brand-500/40");
}

function resetNewProductErrors() {
    if (newProductErrorBox) {
        newProductErrorBox.textContent = "";
        newProductErrorBox.classList.add("hidden");
    }
    newProductFieldInputs.forEach(clearFieldErrorClass);
}

function setNewProductErrorMessages(messages) {
    if (!newProductErrorBox) {
        return;
    }
    newProductErrorBox.innerHTML = messages.map((message) => `<p>${message}</p>`).join("");
    newProductErrorBox.classList.remove("hidden");
}

function markInvalidNewProductFields(messages) {
    const lowerMessages = messages.map((item) => item.toLowerCase());
    newProductFieldInputs.forEach((input) => {
        const key = input.getAttribute("name")?.toLowerCase();
        if (!key) {
            return;
        }
        if (lowerMessages.some((message) => message.includes(key))) {
            fieldErrorClass(input);
        }
    });
}

function hideNewProductModal() {
    if (!newProductOverlay || !newProductPanel) {
        return;
    }
    newProductOverlay.classList.add("opacity-0");
    newProductPanel.classList.add("scale-95", "translate-y-4");
    setTimeout(() => {
        newProductOverlay.classList.add("hidden");
        newProductOverlay.classList.remove("flex");
    }, 180);
}

function showNewProductModal() {
    if (!newProductOverlay || !newProductPanel) {
        return;
    }
    newProductOverlay.classList.remove("hidden");
    newProductOverlay.classList.add("flex");
    requestAnimationFrame(() => {
        newProductOverlay.classList.remove("opacity-0");
        newProductPanel.classList.remove("scale-95", "translate-y-4");
    });
}

async function ensureCategoriesLoaded() {
    if (categoriesLoaded) {
        return;
    }
    try {
        const categories = await fetchCategories();
        renderCategoryOptions(newProductCategorySelect, categories);
        categoriesLoaded = true;
    } catch (error) {
        notify("error", error.message || "No se pudieron cargar las categorías.");
    }
}

async function openNewProductModal() {
    resetNewProductErrors();
    if (newProductForm) {
        newProductForm.reset();
    }
    if (newProductNameInput) {
        newProductNameInput.value = (productSearchInput?.value || "").trim();
    }
    if (newProductCostInput) {
        newProductCostInput.value = unitCostInput?.value || "";
    }
    await ensureCategoriesLoaded();
    showNewProductModal();
    newProductNameInput?.focus();
}

async function handleSubmitNewProduct(event) {
    event.preventDefault();
    resetNewProductErrors();

    const rawPayload = {
        name: newProductNameInput?.value || "",
        category_id: newProductCategorySelect?.value || "",
        cost: newProductCostInput?.value || "",
        sale_price: newProductSalePriceInput?.value || "",
    };
    const validation = validateNewProductPayload(rawPayload);
    if (!validation.isValid) {
        setNewProductErrorMessages(validation.errors);
        markInvalidNewProductFields(validation.errors);
        notify("warning", "Por favor revisa los campos del producto nuevo.");
        return;
    }

    try {
        if (newProductSubmitButton) {
            newProductSubmitButton.disabled = true;
        }
        newProductSubmitSpinner?.classList.remove("hidden");

        const created = await createProduct(validation.payload);

        state.products.push(created);
        state.productsById.set(created.id, created);
        selectProduct(created);
        if (unitCostInput && !unitCostInput.value) {
            unitCostInput.value = created.cost;
        }

        hideNewProductModal();
        notify("success", "Producto creado y seleccionado para esta compra.");
        quantityInput?.focus();
    } catch (error) {
        if (error instanceof ApiError) {
            const apiMessages = formatFastApiValidation(error.details);
            if (apiMessages.length) {
                setNewProductErrorMessages(apiMessages);
                markInvalidNewProductFields(apiMessages);
                notify("error", "Validación fallida. Revisa los detalles del producto.");
            } else {
                setNewProductErrorMessages([error.message]);
                notify("error", error.message);
            }
            return;
        }
        setNewProductErrorMessages([error.message || "Error inesperado al crear el producto."]);
        notify("error", error.message || "Error inesperado al crear el producto.");
    } finally {
        if (newProductSubmitButton) {
            newProductSubmitButton.disabled = false;
        }
        newProductSubmitSpinner?.classList.add("hidden");
    }
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

    newProductButton?.addEventListener("click", openNewProductModal);
    closeNewProductButton?.addEventListener("click", hideNewProductModal);
    cancelNewProductButton?.addEventListener("click", hideNewProductModal);
    newProductOverlay?.addEventListener("click", (event) => {
        if (event.target === newProductOverlay) {
            hideNewProductModal();
        }
    });
    newProductForm?.addEventListener("submit", handleSubmitNewProduct);
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && newProductOverlay && !newProductOverlay.classList.contains("hidden")) {
            hideNewProductModal();
        }
    });
}

wireEvents();
loadSuppliers();
loadProducts();
refreshUI();
