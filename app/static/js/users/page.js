import {
    activateUser,
    ApiError,
    createUser,
    deactivateUser,
    fetchUserById,
    fetchUsers,
    updateUser,
} from "./api.js";
import { createUserModal } from "./modal.js";
import { createUsersState } from "./state.js";
import { clearError, renderUsers, showError } from "./ui.js";
import { formatFastApiValidation, validateUserPayload } from "./validation.js";

const state = createUsersState();
const modal = createUserModal();

const tableBody = document.getElementById("users-table-body");
const errorBox = document.getElementById("users-error");
const openModalButton = document.getElementById("open-user-modal");

function notify(type, message, duration = 3200) {
    window.showToast?.({ type, message, duration });
}

function renderList() {
    if (!tableBody) {
        return;
    }
    renderUsers(tableBody, state.all, window.currentUser?.id);
}

async function loadUsers() {
    if (!errorBox) {
        return;
    }
    try {
        clearError(errorBox);
        state.all = await fetchUsers();
        renderList();
    } catch (error) {
        showError(errorBox, error.message || "No se pudieron cargar los usuarios.");
        notify("error", error.message || "No se pudieron cargar los usuarios.");
    }
}

function openCreateModal() {
    modal.resetErrors();
    modal.setMode("create");
    modal.fillForm(null);
    modal.show();
}

async function openEditModal(userId) {
    try {
        modal.resetErrors();
        modal.setMode("edit");
        modal.setSubmitting(true);
        modal.show();

        const user = await fetchUserById(userId);
        modal.fillForm(user);
    } catch (error) {
        modal.hide();
        showError(errorBox, error.message || "No se pudieron cargar los detalles del usuario.");
        notify("error", error.message || "No se pudieron cargar los detalles del usuario.");
    } finally {
        modal.setSubmitting(false);
    }
}

async function handleSubmitUser(event) {
    event.preventDefault();
    modal.resetErrors();

    const isCreate = modal.getMode() === "create";
    const rawPayload = modal.getRawValues();
    const validation = validateUserPayload(rawPayload, { isCreate });
    if (!validation.isValid) {
        modal.setErrorMessages(validation.errors);
        modal.markInvalidFields(validation.errors);
        notify("warning", "Por favor revisa los campos del formulario.");
        return;
    }

    try {
        modal.setSubmitting(true);

        if (isCreate) {
            await createUser(validation.payload);
        } else {
            await updateUser(modal.getUserId(), validation.payload);
        }

        modal.hide();
        await loadUsers();
        notify("success", isCreate ? "Usuario creado correctamente." : "Usuario actualizado correctamente.");
    } catch (error) {
        if (error instanceof ApiError) {
            const apiMessages = formatFastApiValidation(error.details);
            if (apiMessages.length) {
                modal.setErrorMessages(apiMessages);
                modal.markInvalidFields(apiMessages);
                notify("error", "Validación fallida. Revisa los datos del usuario.");
            } else {
                modal.setErrorMessages([error.message]);
                notify("error", error.message);
            }
            return;
        }
        modal.setErrorMessages([error.message || "Error inesperado al guardar el usuario."]);
        notify("error", error.message || "Error inesperado al guardar el usuario.");
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
    if (!button || button.disabled) {
        return;
    }

    const userId = Number(button.dataset.id);
    const action = button.dataset.action;

    if (action === "edit") {
        openEditModal(userId);
        return;
    }

    if (action === "toggle-active") {
        const isCurrentlyActive = button.dataset.active === "true";
        const userName = button.dataset.name || "este usuario";
        modal.askAction(userId, userName, { isActive: isCurrentlyActive });
    }
}

async function handleConfirmAction(userId) {
    if (!userId) {
        return;
    }
    const user = state.all.find((u) => u.id === userId);
    const isCurrentlyActive = user ? user.is_active : true;

    try {
        if (isCurrentlyActive) {
            await deactivateUser(userId);
            notify("success", "Usuario desactivado.");
        } else {
            await activateUser(userId);
            notify("success", "Usuario activado nuevamente.");
        }
        modal.hideConfirm();
        await loadUsers();
    } catch (error) {
        modal.hideConfirm();
        showError(errorBox, error.message || "No se pudo actualizar el estado del usuario.");
        notify("error", error.message || "No se pudo actualizar el estado del usuario.");
    }
}

function wireEvents() {
    openModalButton?.addEventListener("click", openCreateModal);
    tableBody?.addEventListener("click", handleTableActions);
    modal.form?.addEventListener("submit", handleSubmitUser);
    modal.onConfirmAction(handleConfirmAction);
}

wireEvents();
loadUsers();
