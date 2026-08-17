import {
    activateBusiness,
    activateSuperuser,
    ApiError,
    createBusiness,
    createSuperuser,
    deactivateBusiness,
    deactivateSuperuser,
    fetchBusinesses,
    fetchSuperusers,
} from "./api.js";

function notify(type, message, duration = 3200) {
    window.showToast?.({ type, message, duration });
}

function fadeHide(overlay, panel) {
    if (!overlay || !panel) return;
    overlay.classList.add("opacity-0");
    panel.classList.add("scale-95", "translate-y-4");
    setTimeout(() => {
        overlay.classList.add("hidden");
        overlay.classList.remove("flex");
    }, 180);
}

function fadeShow(overlay, panel) {
    if (!overlay || !panel) return;
    overlay.classList.remove("hidden");
    overlay.classList.add("flex");
    requestAnimationFrame(() => {
        overlay.classList.remove("opacity-0");
        panel.classList.remove("scale-95", "translate-y-4");
    });
}

function fieldErrorClass(input) {
    input.classList.add("border-rose-500", "ring-rose-500/40");
}

function clearFieldErrorClass(input) {
    input.classList.remove("border-rose-500", "ring-rose-500/40");
}

function formatFastApiValidation(details) {
    if (!Array.isArray(details)) {
        return [];
    }
    return details.map((error) => {
        const path = Array.isArray(error.loc) ? error.loc.slice(1).join(".") : "field";
        return `${path}: ${error.msg}`;
    });
}

function initials(name) {
    const words = String(name || "?").trim().split(/\s+/);
    return words.slice(0, 2).map((w) => w[0]?.toUpperCase() || "?").join("");
}

function statusBadge(isActive) {
    return isActive
        ? '<span class="inline-flex rounded-full bg-emerald-500/15 px-2.5 py-1 text-xs font-medium text-emerald-200 ring-1 ring-emerald-500/40">Activo</span>'
        : '<span class="inline-flex rounded-full bg-slate-700/60 px-2.5 py-1 text-xs font-medium text-slate-300 ring-1 ring-slate-600">Inactivo</span>';
}

/* ---------------- Negocios ---------------- */

const businessesErrorBox = document.getElementById("businesses-error");
const businessesTableBody = document.getElementById("businesses-table-body");
const openBusinessModalButton = document.getElementById("open-business-modal");

const businessModalOverlay = document.getElementById("business-modal-overlay");
const businessModalPanel = document.getElementById("business-modal-panel");
const businessForm = document.getElementById("business-form");
const businessModalErrors = document.getElementById("business-modal-errors");
const businessSubmitButton = document.getElementById("submit-business");
const businessSubmitSpinner = document.getElementById("business-submit-spinner");
const businessFieldInputs = Array.from(document.querySelectorAll(".business-field"));

const businessConfirmOverlay = document.getElementById("business-confirm-overlay");
const businessConfirmPanel = document.getElementById("business-confirm-panel");
const businessConfirmTitle = document.getElementById("business-confirm-title");
const businessConfirmMessage = document.getElementById("business-confirm-message");
const confirmBusinessActionButton = document.getElementById("confirm-business-action");

let allBusinesses = [];
let businessConfirmTargetId = null;

function renderBusinesses() {
    if (!businessesTableBody) return;

    if (!allBusinesses.length) {
        businessesTableBody.innerHTML = `
            <tr><td colspan="4" class="px-3 py-8"><div class="saas-empty">Aún no hay negocios. Crea el primero.</div></td></tr>
        `;
        return;
    }

    businessesTableBody.innerHTML = allBusinesses
        .map((business) => {
            const inactive = business.is_active === false;
            const toggleLabel = inactive ? "Activar" : "Desactivar";
            const createdAt = new Date(business.created_at).toLocaleDateString("es-CO", {
                year: "numeric",
                month: "short",
                day: "numeric",
            });
            return `
                <tr class="transition-colors hover:bg-slate-800/50 ${inactive ? "opacity-60" : ""}">
                    <td class="px-3 py-3">
                        <div class="flex items-center gap-3">
                            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500/25 to-cyan-500/20 text-xs font-semibold text-brand-200 ring-1 ring-brand-500/40">${initials(business.name)}</div>
                            <p class="font-medium text-slate-100">${business.name}</p>
                        </div>
                    </td>
                    <td class="px-3 py-3 text-slate-300">${createdAt}</td>
                    <td class="px-3 py-3">${statusBadge(business.is_active)}</td>
                    <td class="px-3 py-3">
                        <div class="flex justify-end">
                            <button
                                data-action="toggle-active"
                                data-id="${business.id}"
                                data-name="${business.name}"
                                data-active="${business.is_active}"
                                class="saas-btn saas-btn-muted rounded-lg px-2.5 py-1.5 text-xs"
                            >${toggleLabel}</button>
                        </div>
                    </td>
                </tr>
            `;
        })
        .join("");
}

async function loadBusinesses() {
    try {
        businessesErrorBox?.classList.add("hidden");
        allBusinesses = await fetchBusinesses();
        renderBusinesses();
    } catch (error) {
        if (businessesErrorBox) {
            businessesErrorBox.textContent = error.message || "No se pudieron cargar los negocios.";
            businessesErrorBox.classList.remove("hidden");
        }
        notify("error", error.message || "No se pudieron cargar los negocios.");
    }
}

function openBusinessModal() {
    businessModalErrors?.classList.add("hidden");
    businessFieldInputs.forEach(clearFieldErrorClass);
    businessForm?.reset();
    fadeShow(businessModalOverlay, businessModalPanel);
}

function hideBusinessModal() {
    fadeHide(businessModalOverlay, businessModalPanel);
}

async function handleSubmitBusiness(event) {
    event.preventDefault();
    businessModalErrors?.classList.add("hidden");
    businessFieldInputs.forEach(clearFieldErrorClass);

    const businessName = document.getElementById("business-name").value.trim();
    const adminFullName = document.getElementById("business-admin-full-name").value.trim();
    const adminEmail = document.getElementById("business-admin-email").value.trim();
    const adminPassword = document.getElementById("business-admin-password").value;

    const errors = [];
    if (!businessName) errors.push("El nombre del negocio es obligatorio.");
    if (!adminFullName) errors.push("El nombre del administrador es obligatorio.");
    if (!adminEmail || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(adminEmail)) errors.push("El correo del administrador no es válido.");
    if (!adminPassword || adminPassword.length < 8) errors.push("La contraseña debe tener al menos 8 caracteres.");

    if (errors.length) {
        if (businessModalErrors) {
            businessModalErrors.innerHTML = errors.map((e) => `<p>${e}</p>`).join("");
            businessModalErrors.classList.remove("hidden");
        }
        notify("warning", "Por favor revisa los campos del formulario.");
        return;
    }

    try {
        businessSubmitButton.disabled = true;
        businessSubmitSpinner?.classList.remove("hidden");

        await createBusiness({
            business_name: businessName,
            admin_full_name: adminFullName,
            admin_email: adminEmail,
            admin_password: adminPassword,
        });

        hideBusinessModal();
        await loadBusinesses();
        notify("success", `Negocio '${businessName}' creado. Ya puedes entregarle sus credenciales a ${adminEmail}.`);
    } catch (error) {
        if (error instanceof ApiError) {
            const apiMessages = formatFastApiValidation(error.details);
            const messages = apiMessages.length ? apiMessages : [error.message];
            if (businessModalErrors) {
                businessModalErrors.innerHTML = messages.map((m) => `<p>${m}</p>`).join("");
                businessModalErrors.classList.remove("hidden");
            }
            notify("error", messages[0]);
            return;
        }
        notify("error", error.message || "No se pudo crear el negocio.");
    } finally {
        businessSubmitButton.disabled = false;
        businessSubmitSpinner?.classList.add("hidden");
    }
}

function handleBusinessTableClick(event) {
    const button = event.target.closest("button[data-action='toggle-active']");
    if (!button) return;

    businessConfirmTargetId = Number(button.dataset.id);
    const isActive = button.dataset.active === "true";
    const name = button.dataset.name || "este negocio";

    if (businessConfirmTitle) {
        businessConfirmTitle.textContent = isActive ? "Desactivar negocio" : "Activar negocio";
    }
    if (businessConfirmMessage) {
        businessConfirmMessage.textContent = isActive
            ? `Al desactivar '${name}', ninguno de sus usuarios podrá iniciar sesión hasta que lo actives de nuevo. ¿Continuar?`
            : `¿Reactivar el negocio '${name}'? Sus usuarios podrán volver a iniciar sesión.`;
    }
    if (confirmBusinessActionButton) {
        confirmBusinessActionButton.textContent = isActive ? "Desactivar" : "Activar";
        confirmBusinessActionButton.classList.toggle("saas-btn-danger", isActive);
        confirmBusinessActionButton.classList.toggle("saas-btn-primary", !isActive);
    }
    fadeShow(businessConfirmOverlay, businessConfirmPanel);
}

async function handleConfirmBusinessAction() {
    if (!businessConfirmTargetId) return;
    const business = allBusinesses.find((b) => b.id === businessConfirmTargetId);
    const isActive = business ? business.is_active : true;

    try {
        if (isActive) {
            await deactivateBusiness(businessConfirmTargetId);
            notify("success", "Negocio desactivado.");
        } else {
            await activateBusiness(businessConfirmTargetId);
            notify("success", "Negocio activado.");
        }
        fadeHide(businessConfirmOverlay, businessConfirmPanel);
        await loadBusinesses();
    } catch (error) {
        fadeHide(businessConfirmOverlay, businessConfirmPanel);
        notify("error", error.message || "No se pudo actualizar el estado del negocio.");
    }
}

/* ---------------- Superusuarios ---------------- */

const superusersErrorBox = document.getElementById("superusers-error");
const superusersTableBody = document.getElementById("superusers-table-body");
const openSuperuserModalButton = document.getElementById("open-superuser-modal");

const superuserModalOverlay = document.getElementById("superuser-modal-overlay");
const superuserModalPanel = document.getElementById("superuser-modal-panel");
const superuserForm = document.getElementById("superuser-form");
const superuserModalErrors = document.getElementById("superuser-modal-errors");
const superuserSubmitButton = document.getElementById("submit-superuser");
const superuserSubmitSpinner = document.getElementById("superuser-submit-spinner");
const superuserFieldInputs = Array.from(document.querySelectorAll(".superuser-field"));

const superuserConfirmOverlay = document.getElementById("superuser-confirm-overlay");
const superuserConfirmPanel = document.getElementById("superuser-confirm-panel");
const superuserConfirmTitle = document.getElementById("superuser-confirm-title");
const superuserConfirmMessage = document.getElementById("superuser-confirm-message");
const confirmSuperuserActionButton = document.getElementById("confirm-superuser-action");

let allSuperusers = [];
let superuserConfirmTargetId = null;

function renderSuperusers() {
    if (!superusersTableBody) return;

    if (!allSuperusers.length) {
        superusersTableBody.innerHTML = `
            <tr><td colspan="4" class="px-3 py-8"><div class="saas-empty">No hay otros superusuarios todavía.</div></td></tr>
        `;
        return;
    }

    superusersTableBody.innerHTML = allSuperusers
        .map((user) => {
            const inactive = user.is_active === false;
            const toggleLabel = inactive ? "Activar" : "Desactivar";
            const isSelf = user.id === window.currentUser?.id;
            return `
                <tr class="transition-colors hover:bg-slate-800/50 ${inactive ? "opacity-60" : ""}">
                    <td class="px-3 py-3">
                        <div class="flex items-center gap-3">
                            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500/25 to-cyan-500/20 text-xs font-semibold text-brand-200 ring-1 ring-brand-500/40">${initials(user.full_name)}</div>
                            <p class="font-medium text-slate-100">${user.full_name}${isSelf ? ' <span class="text-xs text-slate-500">(tú)</span>' : ""}</p>
                        </div>
                    </td>
                    <td class="px-3 py-3 text-slate-300">${user.email}</td>
                    <td class="px-3 py-3">${statusBadge(user.is_active)}</td>
                    <td class="px-3 py-3">
                        <div class="flex justify-end">
                            <button
                                data-action="toggle-active"
                                data-id="${user.id}"
                                data-name="${user.full_name}"
                                data-active="${user.is_active}"
                                class="saas-btn saas-btn-muted rounded-lg px-2.5 py-1.5 text-xs disabled:cursor-not-allowed disabled:opacity-50"
                                ${isSelf ? "disabled" : ""}
                                title="${isSelf ? "No puedes desactivar tu propia cuenta" : ""}"
                            >${toggleLabel}</button>
                        </div>
                    </td>
                </tr>
            `;
        })
        .join("");
}

async function loadSuperusers() {
    try {
        superusersErrorBox?.classList.add("hidden");
        allSuperusers = await fetchSuperusers();
        renderSuperusers();
    } catch (error) {
        if (superusersErrorBox) {
            superusersErrorBox.textContent = error.message || "No se pudieron cargar los superusuarios.";
            superusersErrorBox.classList.remove("hidden");
        }
        notify("error", error.message || "No se pudieron cargar los superusuarios.");
    }
}

function openSuperuserModal() {
    superuserModalErrors?.classList.add("hidden");
    superuserFieldInputs.forEach(clearFieldErrorClass);
    superuserForm?.reset();
    fadeShow(superuserModalOverlay, superuserModalPanel);
}

function hideSuperuserModal() {
    fadeHide(superuserModalOverlay, superuserModalPanel);
}

async function handleSubmitSuperuser(event) {
    event.preventDefault();
    superuserModalErrors?.classList.add("hidden");
    superuserFieldInputs.forEach(clearFieldErrorClass);

    const fullName = document.getElementById("superuser-full-name").value.trim();
    const email = document.getElementById("superuser-email").value.trim();
    const password = document.getElementById("superuser-password").value;

    const errors = [];
    if (!fullName) errors.push("El nombre completo es obligatorio.");
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.push("El correo electrónico no es válido.");
    if (!password || password.length < 8) errors.push("La contraseña debe tener al menos 8 caracteres.");

    if (errors.length) {
        if (superuserModalErrors) {
            superuserModalErrors.innerHTML = errors.map((e) => `<p>${e}</p>`).join("");
            superuserModalErrors.classList.remove("hidden");
        }
        notify("warning", "Por favor revisa los campos del formulario.");
        return;
    }

    try {
        superuserSubmitButton.disabled = true;
        superuserSubmitSpinner?.classList.remove("hidden");

        await createSuperuser({ full_name: fullName, email, password });

        hideSuperuserModal();
        await loadSuperusers();
        notify("success", `Superusuario '${fullName}' creado.`);
    } catch (error) {
        if (error instanceof ApiError) {
            const apiMessages = formatFastApiValidation(error.details);
            const messages = apiMessages.length ? apiMessages : [error.message];
            if (superuserModalErrors) {
                superuserModalErrors.innerHTML = messages.map((m) => `<p>${m}</p>`).join("");
                superuserModalErrors.classList.remove("hidden");
            }
            notify("error", messages[0]);
            return;
        }
        notify("error", error.message || "No se pudo crear el superusuario.");
    } finally {
        superuserSubmitButton.disabled = false;
        superuserSubmitSpinner?.classList.add("hidden");
    }
}

function handleSuperuserTableClick(event) {
    const button = event.target.closest("button[data-action='toggle-active']");
    if (!button || button.disabled) return;

    superuserConfirmTargetId = Number(button.dataset.id);
    const isActive = button.dataset.active === "true";
    const name = button.dataset.name || "este usuario";

    if (superuserConfirmTitle) {
        superuserConfirmTitle.textContent = isActive ? "Desactivar superusuario" : "Activar superusuario";
    }
    if (superuserConfirmMessage) {
        superuserConfirmMessage.textContent = `¿Estás seguro de que deseas ${isActive ? "desactivar" : "activar"} a '${name}'?`;
    }
    if (confirmSuperuserActionButton) {
        confirmSuperuserActionButton.textContent = isActive ? "Desactivar" : "Activar";
        confirmSuperuserActionButton.classList.toggle("saas-btn-danger", isActive);
        confirmSuperuserActionButton.classList.toggle("saas-btn-primary", !isActive);
    }
    fadeShow(superuserConfirmOverlay, superuserConfirmPanel);
}

async function handleConfirmSuperuserAction() {
    if (!superuserConfirmTargetId) return;
    const user = allSuperusers.find((u) => u.id === superuserConfirmTargetId);
    const isActive = user ? user.is_active : true;

    try {
        if (isActive) {
            await deactivateSuperuser(superuserConfirmTargetId);
            notify("success", "Superusuario desactivado.");
        } else {
            await activateSuperuser(superuserConfirmTargetId);
            notify("success", "Superusuario activado.");
        }
        fadeHide(superuserConfirmOverlay, superuserConfirmPanel);
        await loadSuperusers();
    } catch (error) {
        fadeHide(superuserConfirmOverlay, superuserConfirmPanel);
        notify("error", error.message || "No se pudo actualizar el estado del superusuario.");
    }
}

/* ---------------- Wiring ---------------- */

openBusinessModalButton?.addEventListener("click", openBusinessModal);
document.getElementById("close-business-modal")?.addEventListener("click", hideBusinessModal);
document.getElementById("cancel-business-modal")?.addEventListener("click", hideBusinessModal);
businessModalOverlay?.addEventListener("click", (event) => {
    if (event.target === businessModalOverlay) hideBusinessModal();
});
businessForm?.addEventListener("submit", handleSubmitBusiness);
businessesTableBody?.addEventListener("click", handleBusinessTableClick);
document.getElementById("cancel-business-confirm")?.addEventListener("click", () => fadeHide(businessConfirmOverlay, businessConfirmPanel));
businessConfirmOverlay?.addEventListener("click", (event) => {
    if (event.target === businessConfirmOverlay) fadeHide(businessConfirmOverlay, businessConfirmPanel);
});
confirmBusinessActionButton?.addEventListener("click", handleConfirmBusinessAction);

openSuperuserModalButton?.addEventListener("click", openSuperuserModal);
document.getElementById("close-superuser-modal")?.addEventListener("click", hideSuperuserModal);
document.getElementById("cancel-superuser-modal")?.addEventListener("click", hideSuperuserModal);
superuserModalOverlay?.addEventListener("click", (event) => {
    if (event.target === superuserModalOverlay) hideSuperuserModal();
});
superuserForm?.addEventListener("submit", handleSubmitSuperuser);
superusersTableBody?.addEventListener("click", handleSuperuserTableClick);
document.getElementById("cancel-superuser-confirm")?.addEventListener("click", () => fadeHide(superuserConfirmOverlay, superuserConfirmPanel));
superuserConfirmOverlay?.addEventListener("click", (event) => {
    if (event.target === superuserConfirmOverlay) fadeHide(superuserConfirmOverlay, superuserConfirmPanel);
});
confirmSuperuserActionButton?.addEventListener("click", handleConfirmSuperuserAction);

document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    if (businessModalOverlay && !businessModalOverlay.classList.contains("hidden")) hideBusinessModal();
    if (businessConfirmOverlay && !businessConfirmOverlay.classList.contains("hidden")) fadeHide(businessConfirmOverlay, businessConfirmPanel);
    if (superuserModalOverlay && !superuserModalOverlay.classList.contains("hidden")) hideSuperuserModal();
    if (superuserConfirmOverlay && !superuserConfirmOverlay.classList.contains("hidden")) fadeHide(superuserConfirmOverlay, superuserConfirmPanel);
});

loadBusinesses();
loadSuperusers();
