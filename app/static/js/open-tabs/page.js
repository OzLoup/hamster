import {
    ApiError,
    addOpenTabItem,
    closeOpenTab,
    createOpenTab,
    deleteOpenTab,
    fetchOpenTabs,
    fetchProductsForTabs,
    removeOpenTabItem,
} from "./api.js";
import { createOpenTabModals } from "./modal.js";
import { createOpenTabsState } from "./state.js";
import {
    clearMessage,
    currency,
    renderProductSearchOptions,
    renderTabItems,
    renderTabTotal,
    renderTabsGrid,
    setSubmitting,
    showMessage,
} from "./ui.js";

const state = createOpenTabsState();
const modals = createOpenTabModals();

const gridContainer = document.getElementById("open-tabs-grid");
const gridError = document.getElementById("open-tabs-error");
const openNewTabButton = document.getElementById("open-new-tab");

const createForm = document.getElementById("tab-form");
const createNameInput = document.getElementById("tab-name-input");
const createErrors = document.getElementById("tab-modal-errors");
const createSubmitButton = document.getElementById("submit-tab");
const createSubmitSpinner = document.getElementById("tab-submit-spinner");
const createSubmitLabel = document.getElementById("tab-submit-label");

const manageError = document.getElementById("tab-manage-error");
const manageSuccess = document.getElementById("tab-manage-success");
const manageTotal = document.getElementById("tab-manage-total");
const manageItemsBody = document.getElementById("tab-items-body");
const managePayment = document.getElementById("tab-manage-payment");
const productSearchInput = document.getElementById("tab-item-product-search");
const productIdInput = document.getElementById("tab-item-product-id");
const productOptionsList = document.getElementById("tab-item-product-options");
const quantityInput = document.getElementById("tab-item-quantity");
const addItemButton = document.getElementById("add-tab-item");
const closeTabButton = document.getElementById("close-tab-button");
const closeTabSpinner = document.getElementById("close-tab-spinner");
const closeTabLabel = document.getElementById("close-tab-label");

function notify(type, message, duration = 3200) {
    window.showToast?.({ type, message, duration });
}

function normalize(text) {
    return text
        .toString()
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "");
}

let filteredProducts = [];
let activeOptionIndex = -1;

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

function resetAddItemForm() {
    if (productSearchInput) {
        productSearchInput.value = "";
    }
    if (productIdInput) {
        productIdInput.value = "";
    }
    if (quantityInput) {
        quantityInput.value = "1";
    }
}

async function loadProducts() {
    try {
        const products = await fetchProductsForTabs();
        state.products = products;
        state.productsById = new Map(products.map((product) => [product.id, product]));
    } catch (error) {
        notify("error", error.message || "No se pudieron cargar los productos.");
    }
}

async function loadTabs() {
    try {
        clearMessage(gridError);
        const tabs = await fetchOpenTabs();
        state.tabs = tabs;
        state.tabsById = new Map(tabs.map((tab) => [tab.id, tab]));
        renderTabsGrid(gridContainer, tabs);
    } catch (error) {
        showMessage(gridError, error.message || "No se pudieron cargar las cuentas abiertas.");
        notify("error", error.message || "No se pudieron cargar las cuentas abiertas.");
    }
}

function refreshManageModal() {
    const tab = state.tabsById.get(state.activeTabId);
    if (!tab) {
        return;
    }
    renderTabItems(manageItemsBody, tab.items);
    renderTabTotal(manageTotal, tab.total);
}

async function openManageModal(tabId) {
    const tab = state.tabsById.get(tabId);
    if (!tab) {
        return;
    }
    state.activeTabId = tabId;
    clearMessage(manageError);
    clearMessage(manageSuccess);
    resetAddItemForm();
    closeProductOptions();
    if (managePayment) {
        managePayment.value = "";
    }
    modals.showManage(tab.name);
    refreshManageModal();
}

async function handleAddItem() {
    clearMessage(manageError);
    clearMessage(manageSuccess);

    const tabId = state.activeTabId;
    if (!tabId) {
        return;
    }

    const productId = Number(productIdInput?.value);
    const quantity = Number(quantityInput?.value || 0);

    if (!productId) {
        showMessage(manageError, "Por favor selecciona un producto.");
        notify("warning", "Selecciona un producto antes de agregarlo a la cuenta.");
        return;
    }

    if (!Number.isInteger(quantity) || quantity <= 0) {
        showMessage(manageError, "La cantidad debe ser un número entero positivo.");
        notify("warning", "La cantidad debe ser un número entero positivo.");
        return;
    }

    try {
        const updatedTab = await addOpenTabItem(tabId, { product_id: productId, quantity });
        state.tabsById.set(tabId, updatedTab);
        state.tabs = state.tabs.map((tab) => (tab.id === tabId ? updatedTab : tab));
        renderTabsGrid(gridContainer, state.tabs);
        refreshManageModal();
        resetAddItemForm();
        await loadProducts();
    } catch (error) {
        const message = error instanceof ApiError ? error.message : error.message || "No se pudo agregar el producto.";
        showMessage(manageError, message);
        notify("error", message);
    }
}

async function handleRemoveItem(itemId) {
    const tabId = state.activeTabId;
    if (!tabId) {
        return;
    }

    try {
        await removeOpenTabItem(tabId, itemId);
        const tabs = await fetchOpenTabs();
        state.tabs = tabs;
        state.tabsById = new Map(tabs.map((tab) => [tab.id, tab]));
        renderTabsGrid(gridContainer, tabs);
        refreshManageModal();
        await loadProducts();
        notify("success", "Producto quitado de la cuenta.");
    } catch (error) {
        showMessage(manageError, error.message || "No se pudo quitar el producto.");
        notify("error", error.message || "No se pudo quitar el producto.");
    }
}

async function handleCloseTab() {
    clearMessage(manageError);
    clearMessage(manageSuccess);

    const tabId = state.activeTabId;
    const tab = state.tabsById.get(tabId);
    if (!tab) {
        return;
    }

    if (!tab.items.length) {
        showMessage(manageError, "Agrega al menos un producto antes de cobrar la cuenta.");
        notify("warning", "Agrega al menos un producto antes de cobrar la cuenta.");
        return;
    }

    const paymentMethod = managePayment?.value || "";
    if (!paymentMethod) {
        showMessage(manageError, "Selecciona un método de pago.");
        notify("warning", "Selecciona un método de pago antes de cobrar.");
        return;
    }

    try {
        setSubmitting({
            button: closeTabButton,
            spinner: closeTabSpinner,
            label: closeTabLabel,
            isSubmitting: true,
            submittingText: "Cobrando...",
            idleText: "Cobrar y cerrar",
        });

        await closeOpenTab(tabId, { payment_method: paymentMethod });
        showMessage(manageSuccess, "Cuenta cobrada y registrada en ventas.");
        notify("success", `Cuenta '${tab.name}' cobrada y cerrada.`);

        await loadTabs();
        refreshManageModal();
        resetAddItemForm();
        if (managePayment) {
            managePayment.value = "";
        }
    } catch (error) {
        const message = error.message || "No se pudo cerrar la cuenta.";
        showMessage(manageError, message);
        notify("error", message);
    } finally {
        setSubmitting({
            button: closeTabButton,
            spinner: closeTabSpinner,
            label: closeTabLabel,
            isSubmitting: false,
            submittingText: "Cobrando...",
            idleText: "Cobrar y cerrar",
        });
    }
}

async function handleCreateTab(event) {
    event.preventDefault();
    if (createErrors) {
        createErrors.classList.add("hidden");
        createErrors.textContent = "";
    }

    const name = createNameInput?.value.trim() || "";
    if (!name) {
        if (createErrors) {
            createErrors.textContent = "El nombre de la cuenta es obligatorio.";
            createErrors.classList.remove("hidden");
        }
        return;
    }

    try {
        setSubmitting({
            button: createSubmitButton,
            spinner: createSubmitSpinner,
            label: createSubmitLabel,
            isSubmitting: true,
            submittingText: "Creando...",
            idleText: "Crear cuenta",
        });

        await createOpenTab({ name });
        notify("success", `Cuenta '${name}' creada.`);
        modals.hideCreate();
        await loadTabs();
    } catch (error) {
        const message = error.message || "No se pudo crear la cuenta.";
        if (createErrors) {
            createErrors.textContent = message;
            createErrors.classList.remove("hidden");
        }
        notify("error", message);
    } finally {
        setSubmitting({
            button: createSubmitButton,
            spinner: createSubmitSpinner,
            label: createSubmitLabel,
            isSubmitting: false,
            submittingText: "Creando...",
            idleText: "Crear cuenta",
        });
    }
}

function handleGridClick(event) {
    const manageButton = event.target.closest("button[data-action='manage']");
    if (manageButton) {
        openManageModal(Number(manageButton.dataset.id));
        return;
    }

    const deleteButton = event.target.closest("button[data-action='delete']");
    if (deleteButton) {
        const tabId = Number(deleteButton.dataset.id);
        const tab = state.tabsById.get(tabId);
        if (!tab) {
            return;
        }
        const message = tab.items.length
            ? `La cuenta '${tab.name}' tiene ${tab.items.length} producto(s) sin cobrar por ${currency(tab.total)}. El stock será restaurado. ¿Deseas eliminarla de todas formas?`
            : `¿Estás seguro de que deseas eliminar la cuenta '${tab.name}'?`;
        modals.showConfirm(tabId, message);
    }
}

function handleItemsBodyClick(event) {
    const button = event.target.closest("button[data-action='remove-item']");
    if (!button) {
        return;
    }
    handleRemoveItem(Number(button.dataset.id));
}

async function handleConfirmDelete(tabId) {
    if (!tabId) {
        return;
    }
    try {
        await deleteOpenTab(tabId);
        modals.hideConfirm();
        notify("success", "Cuenta eliminada.");
        if (state.activeTabId === tabId) {
            modals.hideManage();
            state.activeTabId = null;
        }
        await loadTabs();
        await loadProducts();
    } catch (error) {
        notify("error", error.message || "No se pudo eliminar la cuenta.");
    }
}

function wireEvents() {
    openNewTabButton?.addEventListener("click", modals.showCreate);
    createForm?.addEventListener("submit", handleCreateTab);
    gridContainer?.addEventListener("click", handleGridClick);
    manageItemsBody?.addEventListener("click", handleItemsBodyClick);
    addItemButton?.addEventListener("click", handleAddItem);
    closeTabButton?.addEventListener("click", handleCloseTab);
    modals.onConfirmDelete(handleConfirmDelete);

    productSearchInput?.addEventListener("input", handleProductSearchInput);
    productSearchInput?.addEventListener("focus", openProductOptions);
    productSearchInput?.addEventListener("keydown", handleProductSearchKeydown);
    productOptionsList?.addEventListener("click", handleProductOptionsClick);
    document.addEventListener("click", handleOutsideProductClick);
}

wireEvents();
loadProducts();
loadTabs();
