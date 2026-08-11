function fadeHide(overlay, panel) {
    if (!overlay || !panel) {
        return;
    }
    overlay.classList.add("opacity-0");
    panel.classList.add("scale-95", "translate-y-4");
    setTimeout(() => {
        overlay.classList.add("hidden");
        overlay.classList.remove("flex");
    }, 180);
}

function fadeShow(overlay, panel) {
    if (!overlay || !panel) {
        return;
    }
    overlay.classList.remove("hidden");
    overlay.classList.add("flex");
    requestAnimationFrame(() => {
        overlay.classList.remove("opacity-0");
        panel.classList.remove("scale-95", "translate-y-4");
    });
}

export function createOpenTabModals() {
    const createOverlay = document.getElementById("tab-modal-overlay");
    const createPanel = document.getElementById("tab-modal-panel");
    const createForm = document.getElementById("tab-form");
    const createErrors = document.getElementById("tab-modal-errors");
    const createNameInput = document.getElementById("tab-name-input");

    const manageOverlay = document.getElementById("tab-manage-overlay");
    const managePanel = document.getElementById("tab-manage-panel");
    const manageTitle = document.getElementById("tab-manage-title");

    const confirmOverlay = document.getElementById("tab-confirm-overlay");
    const confirmPanel = document.getElementById("tab-confirm-panel");
    const confirmMessage = document.getElementById("tab-confirm-message");
    const confirmDeleteButton = document.getElementById("confirm-tab-delete");

    let deleteTargetId = null;

    const hideCreate = () => fadeHide(createOverlay, createPanel);
    const showCreate = () => {
        createErrors?.classList.add("hidden");
        if (createErrors) {
            createErrors.textContent = "";
        }
        createForm?.reset();
        fadeShow(createOverlay, createPanel);
        createNameInput?.focus();
    };

    const hideManage = () => fadeHide(manageOverlay, managePanel);
    const showManage = (tabName) => {
        if (manageTitle) {
            manageTitle.textContent = tabName;
        }
        fadeShow(manageOverlay, managePanel);
    };

    const hideConfirm = () => fadeHide(confirmOverlay, confirmPanel);
    const showConfirm = (tabId, message) => {
        deleteTargetId = tabId;
        if (confirmMessage) {
            confirmMessage.textContent = message;
        }
        fadeShow(confirmOverlay, confirmPanel);
    };

    document.getElementById("close-tab-modal")?.addEventListener("click", hideCreate);
    document.getElementById("cancel-tab-modal")?.addEventListener("click", hideCreate);
    createOverlay?.addEventListener("click", (event) => {
        if (event.target === createOverlay) {
            hideCreate();
        }
    });

    document.getElementById("close-tab-manage")?.addEventListener("click", hideManage);
    manageOverlay?.addEventListener("click", (event) => {
        if (event.target === manageOverlay) {
            hideManage();
        }
    });

    document.getElementById("cancel-tab-delete")?.addEventListener("click", hideConfirm);
    confirmOverlay?.addEventListener("click", (event) => {
        if (event.target === confirmOverlay) {
            hideConfirm();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") {
            return;
        }
        if (createOverlay && !createOverlay.classList.contains("hidden")) {
            hideCreate();
        }
        if (manageOverlay && !manageOverlay.classList.contains("hidden")) {
            hideManage();
        }
        if (confirmOverlay && !confirmOverlay.classList.contains("hidden")) {
            hideConfirm();
        }
    });

    return {
        showCreate,
        hideCreate,
        showManage,
        hideManage,
        showConfirm,
        hideConfirm,
        onConfirmDelete: (handler) => confirmDeleteButton?.addEventListener("click", () => handler(deleteTargetId)),
    };
}
