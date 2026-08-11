import {
    activateSupplier,
    ApiError,
    createSupplier,
    deactivateSupplier,
    deleteSupplier,
    fetchSupplierById,
    fetchSuppliers,
    updateSupplier,
} from "./api.js";
import { createSupplierModal } from "./modal.js";
import { createSuppliersState } from "./state.js";
import { clearError, renderSuppliers, showError } from "./ui.js";
import { formatFastApiValidation, validateSupplierPayload } from "./validation.js";

const state = createSuppliersState();
const modal = createSupplierModal();

const tableBody = document.getElementById("suppliers-table-body");
const searchInput = document.getElementById("supplier-search");
const errorBox = document.getElementById("suppliers-error");
const openModalButton = document.getElementById("open-supplier-modal");

let searchDebounceTimer;

function notify(type, message, duration = 3200) {
    window.showToast?.({ type, message, duration });
}

function applyFilter() {
    const query = (state.search || "").toLowerCase();
    state.filtered = state.all.filter((supplier) => {
        if (!query) {
            return true;
        }
        const name = String(supplier.name || "").toLowerCase();
        const contact = String(supplier.contact_name || "").toLowerCase();
        return name.includes(query) || contact.includes(query);
    });
}

function renderList() {
    if (!tableBody) {
        return;
    }
    renderSuppliers(tableBody, state.filtered);
}

async function loadSuppliers() {
    if (!errorBox) {
        return;
    }

    try {
        clearError(errorBox);
        state.all = await fetchSuppliers();
        applyFilter();
        renderList();
    } catch (error) {
        showError(errorBox, error.message || "No se pudieron cargar los proveedores.");
        notify("error", error.message || "No se pudieron cargar los proveedores.");
    }
}

function openCreateModal() {
    modal.resetErrors();
    modal.setMode("create");
    modal.fillForm(null);
    modal.show();
}

async function openEditModal(supplierId) {
    try {
        modal.resetErrors();
        modal.setMode("edit");
        modal.setSubmitting(true);
        modal.show();

        const supplier = await fetchSupplierById(supplierId);
        modal.fillForm(supplier);
    } catch (error) {
        modal.hide();
        showError(errorBox, error.message || "No se pudieron cargar los detalles del proveedor.");
        notify("error", error.message || "No se pudieron cargar los detalles del proveedor.");
    } finally {
        modal.setSubmitting(false);
    }
}

async function handleSubmitSupplier(event) {
    event.preventDefault();
    modal.resetErrors();

    const rawPayload = modal.getRawValues();
    const validation = validateSupplierPayload(rawPayload);
    if (!validation.isValid) {
        modal.setErrorMessages(validation.errors);
        modal.markInvalidFields(validation.errors);
        notify("warning", "Por favor revisa los campos del formulario de proveedor.");
        return;
    }

    try {
        modal.setSubmitting(true);

        if (modal.getMode() === "edit") {
            await updateSupplier(modal.getSupplierId(), validation.payload);
        } else {
            await createSupplier(validation.payload);
        }

        modal.hide();
        await loadSuppliers();
        notify(
            "success",
            modal.getMode() === "edit" ? "Proveedor actualizado correctamente." : "Proveedor creado correctamente."
        );
    } catch (error) {
        if (error instanceof ApiError) {
            const apiMessages = formatFastApiValidation(error.details);
            if (apiMessages.length) {
                modal.setErrorMessages(apiMessages);
                modal.markInvalidFields(apiMessages);
                notify("error", "Validación fallida. Revisa los detalles del proveedor.");
            } else {
                modal.setErrorMessages([error.message]);
                notify("error", error.message);
            }
            return;
        }

        modal.setErrorMessages([error.message || "Error inesperado al guardar el proveedor."]);
        notify("error", error.message || "Error inesperado al guardar el proveedor.");
    } finally {
        modal.setSubmitting(false);
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

    const supplierId = Number(button.dataset.id);
    const action = button.dataset.action;

    if (action === "edit") {
        openEditModal(supplierId);
        return;
    }

    if (action === "toggle-active") {
        const isCurrentlyActive = button.dataset.active === "true";
        toggleSupplierActive(supplierId, isCurrentlyActive);
        return;
    }

    if (action === "delete") {
        const supplierName = button.dataset.name || "este proveedor";
        modal.askDelete(supplierId, supplierName);
    }
}

async function toggleSupplierActive(supplierId, isCurrentlyActive) {
    try {
        if (isCurrentlyActive) {
            await deactivateSupplier(supplierId);
            notify("success", "Proveedor desactivado. Ya no podrá recibir nuevas compras.");
        } else {
            await activateSupplier(supplierId);
            notify("success", "Proveedor activado nuevamente.");
        }
        await loadSuppliers();
    } catch (error) {
        showError(errorBox, error.message || "No se pudo actualizar el estado del proveedor.");
        notify("error", error.message || "No se pudo actualizar el estado del proveedor.");
    }
}

async function confirmDelete(supplierId) {
    if (!supplierId) {
        return;
    }

    try {
        await deleteSupplier(supplierId);
        modal.hideConfirm();
        await loadSuppliers();
        notify("success", "Proveedor eliminado correctamente.");
    } catch (error) {
        modal.hideConfirm();
        const message =
            error?.status === 409
                ? "No se puede eliminar este proveedor porque tiene compras registradas asociadas."
                : error.message || "No se pudo eliminar el proveedor.";
        showError(errorBox, message);
        notify("error", message);
    }
}

function wireEvents() {
    openModalButton?.addEventListener("click", openCreateModal);

    searchInput?.addEventListener("input", () => {
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = window.setTimeout(() => {
            state.search = (searchInput.value || "").trim();
            applyFilter();
            renderList();
        }, 250);
    });

    tableBody?.addEventListener("click", handleTableActions);
    modal.form?.addEventListener("submit", handleSubmitSupplier);
    modal.onConfirmDelete(confirmDelete);
}

wireEvents();
loadSuppliers();
