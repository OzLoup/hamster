import {
    ApiError,
    createProduct,
    deleteProduct,
    fetchCategories,
    fetchProductById,
    fetchProducts,
    updateProduct,
} from "./api.js";
import { createProductModal } from "./modal.js";
import { createProductsState } from "./state.js";
import { clearError, renderPagination, renderProducts, showError } from "./ui.js";
import { formatFastApiValidation, validateProductPayload } from "./validation.js";

const state = createProductsState();
const modal = createProductModal();

const tableBody = document.getElementById("products-table-body");
const prevButton = document.getElementById("products-prev");
const nextButton = document.getElementById("products-next");
const pageIndicator = document.getElementById("products-page-indicator");
const meta = document.getElementById("products-meta");
const searchInput = document.getElementById("product-search");
const errorBox = document.getElementById("products-error");
const openModalButton = document.getElementById("open-product-modal");

let searchDebounceTimer;
let categoriesById = new Map();
let categories = [];
let pendingDeleteId = null;

function notify(type, message, duration = 3200) {
    window.showToast?.({ type, message, duration });
}

async function loadCategories() {
    try {
        categories = await fetchCategories();
        categoriesById = new Map(categories.map((category) => [category.id, category.name]));
        modal.setCategories(categories);
    } catch {
        categories = [];
        categoriesById = new Map();
        modal.setCategories([]);
    }
}

async function loadProducts() {
    if (!tableBody || !prevButton || !nextButton || !pageIndicator || !meta || !errorBox) {
        return;
    }

    try {
        clearError(errorBox);
        const payload = await fetchProducts({
            page: state.page,
            pageSize: state.pageSize,
            search: state.search,
        });

        state.total = payload.total;
        state.totalPages = Math.max(payload.total_pages || 1, 1);
        renderProducts(tableBody, payload.items || [], categoriesById);
        renderPagination({
            state,
            count: (payload.items || []).length,
            prevButton,
            nextButton,
            pageIndicator,
            meta,
        });
    } catch (error) {
        showError(errorBox, error.message || "No se pudieron cargar los productos.");
    }
}

function handleTableActions(event) {
    const target = event.target;
    if (!(target instanceof HTMLElement)) {
        return;
    }

    const button = target.closest("button[data-action]");
    if (!button) {
        return;
    }

    const productId = Number(button.dataset.id);
    const action = button.dataset.action;

    if (action === "view") {
        notify("info", `La acción Ver para el producto #${productId} aún no está implementada.`);
        return;
    }

    if (action === "edit") {
        openEditModal(productId);
        return;
    }

    if (action === "delete") {
        if (pendingDeleteId !== productId) {
            pendingDeleteId = productId;
            notify("warning", "Haz clic en Eliminar nuevamente para confirmar la eliminación del producto.", 2600);
            return;
        }

        pendingDeleteId = null;
        deleteProduct(productId)
            .then(() => {
                notify("success", "Producto eliminado correctamente.");
                if (state.page > 1 && state.total <= (state.page - 1) * state.pageSize + 1) {
                    state.page -= 1;
                }
                return loadProducts();
            })
            .catch((error) => {
                if (errorBox) {
                    showError(errorBox, error.message || "No se pudo eliminar el producto.");
                }
                notify("error", error.message || "No se pudo eliminar el producto.");
            });
    }
}

document.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) {
        return;
    }
    if (!target.closest("button[data-action='delete']")) {
        pendingDeleteId = null;
    }
});

async function openEditModal(productId) {
    try {
        modal.resetErrors();
        modal.setMode("edit");
        modal.setSubmitting(true);
        modal.show();

        const product = await fetchProductById(productId);
        modal.fillForm(product);
    } catch (error) {
        modal.hide();
        showError(errorBox, error.message || "No se pudieron cargar los detalles del producto.");
        notify("error", error.message || "No se pudieron cargar los detalles del producto.");
    } finally {
        modal.setSubmitting(false);
    }
}

function openCreateModal() {
    modal.resetErrors();
    modal.setMode("create");
    modal.fillForm(null);
    modal.show();
}

async function handleSubmitProduct(event) {
    event.preventDefault();
    modal.resetErrors();

    const rawPayload = modal.getRawValues();
    const validation = validateProductPayload(rawPayload);
    if (!validation.isValid) {
        modal.setErrorMessages(validation.errors);
        modal.markInvalidFields(validation.errors);
        notify("warning", "Por favor revisa los campos destacados del formulario de producto.");
        return;
    }

    try {
        modal.setSubmitting(true);

        if (modal.getMode() === "edit") {
            await updateProduct(modal.getProductId(), validation.payload);
        } else {
            await createProduct(validation.payload);
        }

        modal.hide();
        state.page = 1;
        await loadProducts();
        notify(
            "success",
            modal.getMode() === "edit" ? "Producto actualizado correctamente." : "Producto creado correctamente."
        );
    } catch (error) {
        if (error instanceof ApiError) {
            const apiMessages = formatFastApiValidation(error.details);
            if (apiMessages.length) {
                modal.setErrorMessages(apiMessages);
                modal.markInvalidFields(apiMessages);
                notify("error", "Validación fallida. Revisa los detalles del formulario.");
            } else {
                modal.setErrorMessages([error.message]);
                notify("error", error.message);
            }
            return;
        }

        modal.setErrorMessages([error.message || "Error inesperado al guardar el producto."]);
        notify("error", error.message || "Error inesperado al guardar el producto.");
    } finally {
        modal.setSubmitting(false);
    }
}

function wireEvents() {
    openModalButton?.addEventListener("click", openCreateModal);

    prevButton?.addEventListener("click", () => {
        if (state.page > 1) {
            state.page -= 1;
            loadProducts();
        }
    });

    nextButton?.addEventListener("click", () => {
        if (state.page < state.totalPages) {
            state.page += 1;
            loadProducts();
        }
    });

    searchInput?.addEventListener("input", () => {
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = window.setTimeout(() => {
            state.search = (searchInput.value || "").trim();
            state.page = 1;
            loadProducts();
        }, 300);
    });

    tableBody?.addEventListener("click", handleTableActions);
    modal.form?.addEventListener("submit", handleSubmitProduct);
}

wireEvents();
loadCategories().then(loadProducts);
