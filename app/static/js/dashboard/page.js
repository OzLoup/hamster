import { ApiError, fetchDashboardSummary, fetchLowStockProducts } from "./api.js";

const errorBox = document.getElementById("dashboard-error");

const openLowStockButton = document.getElementById("open-low-stock-modal");
const lowStockOverlay = document.getElementById("low-stock-modal-overlay");
const lowStockPanel = document.getElementById("low-stock-modal-panel");
const closeLowStockButton = document.getElementById("close-low-stock-modal");
const lowStockModalErrorBox = document.getElementById("low-stock-modal-error");
const lowStockModalBody = document.getElementById("low-stock-modal-body");

const totalProductsEl = document.getElementById("stat-total-products");
const catalogHealthWrap = document.getElementById("stat-catalog-health-wrap");
const catalogHealthLabel = document.getElementById("stat-catalog-health-label");

const totalCategoriesEl = document.getElementById("stat-total-categories");
const categoryBalanceWrap = document.getElementById("stat-category-balance-wrap");
const categoryBalanceLabel = document.getElementById("stat-category-balance-label");

const salesMonthEl = document.getElementById("stat-sales-month");
const salesTodayEl = document.getElementById("stat-sales-today");
const salesTrendWrap = document.getElementById("stat-sales-trend-wrap");
const salesTrendLabel = document.getElementById("stat-sales-trend-label");

const revenueTodayEl = document.getElementById("stat-revenue-today");
const revenueChangeWrap = document.getElementById("stat-revenue-change-wrap");
const revenueChangeLabel = document.getElementById("stat-revenue-change-label");

const lowStockEl = document.getElementById("stat-low-stock");

const LEVEL_STYLES = {
    positive: { dot: "bg-emerald-400", text: "text-emerald-300" },
    neutral: { dot: "bg-slate-400", text: "text-slate-400" },
    warning: { dot: "bg-amber-400", text: "text-amber-300" },
    critical: { dot: "bg-rose-400", text: "text-rose-300" },
};

function currency(value) {
    const amount = Number(value);
    if (Number.isNaN(amount)) {
        return "$ 0";
    }
    return new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP",
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    }).format(amount);
}

function applyInsight(wrapEl, labelEl, insight) {
    if (!wrapEl || !labelEl || !insight) {
        return;
    }
    const dot = wrapEl.querySelector("span:first-child");
    const style = LEVEL_STYLES[insight.level] || LEVEL_STYLES.neutral;
    if (dot) {
        dot.className = `h-2 w-2 rounded-full ${style.dot}`;
    }
    labelEl.className = style.text;
    labelEl.textContent = insight.label;
}

function revenueChangeInsight(pct) {
    if (pct === null || pct === undefined) {
        return { level: "neutral", label: "Sin ventas registradas ayer" };
    }
    const value = Number(pct);
    const sign = value > 0 ? "+" : "";
    const label = `${sign}${value.toFixed(1)}% vs. ayer`;
    if (value > 0) {
        return { level: "positive", label };
    }
    if (value < 0) {
        return { level: "warning", label };
    }
    return { level: "neutral", label };
}

function hideLowStockModal() {
    if (!lowStockOverlay || !lowStockPanel) {
        return;
    }
    lowStockOverlay.classList.add("opacity-0");
    lowStockPanel.classList.add("scale-95", "translate-y-4");
    setTimeout(() => {
        lowStockOverlay.classList.add("hidden");
        lowStockOverlay.classList.remove("flex");
    }, 180);
}

function showLowStockModal() {
    if (!lowStockOverlay || !lowStockPanel) {
        return;
    }
    lowStockOverlay.classList.remove("hidden");
    lowStockOverlay.classList.add("flex");
    requestAnimationFrame(() => {
        lowStockOverlay.classList.remove("opacity-0");
        lowStockPanel.classList.remove("scale-95", "translate-y-4");
    });
}

function renderLowStockTable(products) {
    if (!lowStockModalBody) {
        return;
    }

    if (!products.length) {
        lowStockModalBody.innerHTML = `
            <tr>
                <td colspan="3" class="px-3 py-8">
                    <div class="saas-empty">No hay productos con bajo stock en este momento.</div>
                </td>
            </tr>
        `;
        return;
    }

    lowStockModalBody.innerHTML = products
        .map(
            (product) => `
                <tr class="transition-colors hover:bg-slate-800/40">
                    <td class="px-3 py-3">
                        <p class="font-medium text-slate-100">${product.name}</p>
                        <p class="text-xs text-slate-400">SKU: ${product.sku}</p>
                    </td>
                    <td class="px-3 py-3 text-slate-300">${product.category_name}</td>
                    <td class="px-3 py-3 text-right text-rose-300">${product.stock_quantity}</td>
                </tr>
            `
        )
        .join("");
}

async function openLowStockModal() {
    showLowStockModal();
    if (lowStockModalErrorBox) {
        lowStockModalErrorBox.textContent = "";
        lowStockModalErrorBox.classList.add("hidden");
    }
    if (lowStockModalBody) {
        lowStockModalBody.innerHTML = `
            <tr>
                <td colspan="3" class="px-3 py-8">
                    <div class="saas-empty animate-pulseSoft">Cargando…</div>
                </td>
            </tr>
        `;
    }

    try {
        const products = await fetchLowStockProducts();
        renderLowStockTable(products);
    } catch (error) {
        if (lowStockModalErrorBox) {
            const message = error instanceof ApiError ? error.message : "No se pudieron cargar los productos.";
            lowStockModalErrorBox.textContent = message;
            lowStockModalErrorBox.classList.remove("hidden");
        }
        renderLowStockTable([]);
    }
}

function wireLowStockModalEvents() {
    openLowStockButton?.addEventListener("click", openLowStockModal);
    closeLowStockButton?.addEventListener("click", hideLowStockModal);
    lowStockOverlay?.addEventListener("click", (event) => {
        if (event.target === lowStockOverlay) {
            hideLowStockModal();
        }
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && lowStockOverlay && !lowStockOverlay.classList.contains("hidden")) {
            hideLowStockModal();
        }
    });
}

async function loadDashboard() {
    try {
        const summary = await fetchDashboardSummary();

        if (totalProductsEl) {
            totalProductsEl.textContent = String(summary.total_products);
        }
        applyInsight(catalogHealthWrap, catalogHealthLabel, summary.catalog_health);

        if (totalCategoriesEl) {
            totalCategoriesEl.textContent = String(summary.total_categories);
        }
        applyInsight(categoryBalanceWrap, categoryBalanceLabel, summary.category_balance);

        if (salesMonthEl) {
            salesMonthEl.textContent = String(summary.sales_this_month);
        }
        if (salesTodayEl) {
            salesTodayEl.textContent = String(summary.sales_today);
        }
        applyInsight(salesTrendWrap, salesTrendLabel, summary.sales_trend);

        if (revenueTodayEl) {
            revenueTodayEl.textContent = currency(summary.revenue_today);
        }
        applyInsight(revenueChangeWrap, revenueChangeLabel, revenueChangeInsight(summary.revenue_change_pct));

        if (lowStockEl) {
            lowStockEl.textContent = String(summary.low_stock_products);
        }
    } catch (error) {
        if (errorBox) {
            const message = error instanceof ApiError ? error.message : "No se pudo cargar el panel.";
            errorBox.textContent = message;
            errorBox.classList.remove("hidden");
        }
    }
}

wireLowStockModalEvents();
loadDashboard();
