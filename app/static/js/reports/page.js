import {
    ApiError,
    fetchAppSettings,
    fetchProductsForReports,
    fetchPurchasesForReports,
    fetchSalesForReports,
    fetchSuppliersForReports,
} from "./api.js";
import { buildAndDownloadReportsPdf, buildReportsCsv, downloadCsv } from "./export.js";
import {
    renderDailySalesChart,
    renderLowStock,
    renderMonthlyPurchasesChart,
    renderMonthlyRevenueChart,
    renderStats,
    renderTopProducts,
    renderTopSuppliers,
    showReportsError,
} from "./ui.js";

const exportButton = document.getElementById("export-report");
const exportPdfButton = document.getElementById("export-report-pdf");
const presetSelect = document.getElementById("report-filter-preset");
const startInput = document.getElementById("report-filter-start");
const endInput = document.getElementById("report-filter-end");
const clearButton = document.getElementById("report-filter-clear");
const filterSummary = document.getElementById("report-filter-summary");
const dailyChartLabel = document.getElementById("reports-daily-chart-label");
const monthlyChartLabel = document.getElementById("reports-monthly-chart-label");
const purchasesChartLabel = document.getElementById("reports-purchases-chart-label");

let rawSales = [];
let rawPurchases = [];
let rawProducts = [];
let rawSuppliers = [];
let businessName = "Hamster";
let currentRange = { start: null, end: null };
let latestReportData = null;

function notify(type, message, duration = 3200) {
    window.showToast?.({ type, message, duration });
}

function isoDate(date) {
    return date.toISOString().slice(0, 10);
}

function monthKey(date) {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

function monthLabel(key) {
    const [year, month] = key.split("-").map(Number);
    const date = new Date(year, month - 1, 1);
    return new Intl.DateTimeFormat("es-419", { month: "short", year: "2-digit" }).format(date);
}

function startOfDay(date) {
    const d = new Date(date);
    d.setHours(0, 0, 0, 0);
    return d;
}

function endOfDay(date) {
    const d = new Date(date);
    d.setHours(23, 59, 59, 999);
    return d;
}

function addDays(date, days) {
    const d = new Date(date);
    d.setDate(d.getDate() + days);
    return d;
}

function daysBetween(start, end) {
    return Math.round((startOfDay(end) - startOfDay(start)) / (1000 * 60 * 60 * 24));
}

function toDatetimeLocalValue(date) {
    if (!date) {
        return "";
    }
    const pad = (n) => String(n).padStart(2, "0");
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function parseDatetimeLocalValue(value) {
    if (!value) {
        return null;
    }
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : date;
}

function computePresetRange(preset) {
    const now = new Date();
    switch (preset) {
        case "today":
            return { start: startOfDay(now), end: endOfDay(now) };
        case "yesterday": {
            const y = addDays(now, -1);
            return { start: startOfDay(y), end: endOfDay(y) };
        }
        case "last7":
            return { start: startOfDay(addDays(now, -6)), end: endOfDay(now) };
        case "last30":
            return { start: startOfDay(addDays(now, -29)), end: endOfDay(now) };
        case "thisMonth":
            return { start: new Date(now.getFullYear(), now.getMonth(), 1, 0, 0, 0, 0), end: endOfDay(now) };
        case "all":
        default:
            return { start: null, end: null };
    }
}

function filterEntriesByRange(entries, range) {
    if (!range.start && !range.end) {
        return entries;
    }
    return entries.filter((entry) => {
        const t = new Date(entry.created_at);
        if (range.start && t < range.start) {
            return false;
        }
        if (range.end && t > range.end) {
            return false;
        }
        return true;
    });
}

function resolveRangeBounds(range, entries) {
    const end = range.end || new Date();
    if (range.start) {
        return { start: range.start, end };
    }
    if (entries.length) {
        const oldest = entries.reduce((min, entry) => {
            const t = new Date(entry.created_at);
            return t < min ? t : min;
        }, new Date(entries[0].created_at));
        return { start: startOfDay(oldest), end };
    }
    return { start: startOfDay(addDays(end, -6)), end };
}

function formatRangeSummary(range, count) {
    if (!range.start && !range.end) {
        return `Mostrando todas las ventas registradas (${count}).`;
    }
    const fmt = new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeStyle: "short" });
    if (range.start && range.end) {
        return `Mostrando ${count} venta(s) entre ${fmt.format(range.start)} y ${fmt.format(range.end)}.`;
    }
    if (range.start) {
        return `Mostrando ${count} venta(s) desde ${fmt.format(range.start)}.`;
    }
    return `Mostrando ${count} venta(s) hasta ${fmt.format(range.end)}.`;
}

function formatRangeLabel(range) {
    if (!range.start && !range.end) {
        return "Todo el tiempo";
    }
    const fmt = new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeStyle: "short" });
    if (range.start && range.end) {
        return `${fmt.format(range.start)} — ${fmt.format(range.end)}`;
    }
    if (range.start) {
        return `Desde ${fmt.format(range.start)}`;
    }
    return `Hasta ${fmt.format(range.end)}`;
}

function buildTopProducts(products, sales) {
    const productMap = new Map(products.map((product) => [product.id, product]));
    const aggregate = new Map();

    sales.forEach((sale) => {
        (sale.sale_items || []).forEach((line) => {
            const current = aggregate.get(line.product_id) || { quantity: 0, revenue: 0 };
            current.quantity += Number(line.quantity || 0);
            current.revenue += Number(line.subtotal || 0);
            aggregate.set(line.product_id, current);
        });
    });

    return Array.from(aggregate.entries())
        .map(([productId, stats]) => ({
            name: productMap.get(productId)?.name || `Producto #${productId}`,
            quantity: stats.quantity,
            revenue: Number(stats.revenue.toFixed(2)),
        }))
        .sort((a, b) => b.quantity - a.quantity)
        .slice(0, 5);
}

function buildTopSuppliers(suppliers, purchases) {
    const supplierMap = new Map(suppliers.map((supplier) => [supplier.id, supplier]));
    const aggregate = new Map();

    purchases.forEach((purchase) => {
        const current = aggregate.get(purchase.supplier_id) || { amount: 0, count: 0 };
        current.amount += Number(purchase.total_amount || 0);
        current.count += 1;
        aggregate.set(purchase.supplier_id, current);
    });

    return Array.from(aggregate.entries())
        .map(([supplierId, stats]) => ({
            name: supplierMap.get(supplierId)?.name || `Proveedor #${supplierId}`,
            amount: Number(stats.amount.toFixed(2)),
            count: stats.count,
        }))
        .sort((a, b) => b.amount - a.amount)
        .slice(0, 5);
}

function totalAmount(entries) {
    return entries.reduce((sum, entry) => sum + Number(entry.total_amount || 0), 0);
}

function buildFixedDailySeries(sales) {
    const map = new Map();
    const today = new Date();

    for (let i = 6; i >= 0; i -= 1) {
        map.set(isoDate(addDays(today, -i)), 0);
    }

    sales.forEach((sale) => {
        const key = isoDate(new Date(sale.created_at));
        if (map.has(key)) {
            map.set(key, map.get(key) + Number(sale.total_amount || 0));
        }
    });

    const labels = Array.from(map.keys()).map((key) => {
        const date = new Date(`${key}T00:00:00`);
        return new Intl.DateTimeFormat("es-419", { weekday: "short" }).format(date);
    });
    const values = Array.from(map.values()).map((value) => Number(value.toFixed(2)));

    return { labels, values };
}

function buildFixedMonthlySeries(sales) {
    const map = new Map();
    const now = new Date();

    for (let i = 5; i >= 0; i -= 1) {
        map.set(monthKey(new Date(now.getFullYear(), now.getMonth() - i, 1)), 0);
    }

    sales.forEach((sale) => {
        const key = monthKey(new Date(sale.created_at));
        if (map.has(key)) {
            map.set(key, map.get(key) + Number(sale.total_amount || 0));
        }
    });

    const labels = Array.from(map.keys()).map(monthLabel);
    const values = Array.from(map.values()).map((value) => Number(value.toFixed(2)));

    return { labels, values };
}

function bucketByDay(sales, start, end) {
    const map = new Map();
    const spanDays = daysBetween(start, end);
    for (let i = 0; i <= spanDays; i += 1) {
        map.set(isoDate(addDays(startOfDay(start), i)), 0);
    }

    sales.forEach((sale) => {
        const key = isoDate(new Date(sale.created_at));
        if (map.has(key)) {
            map.set(key, map.get(key) + Number(sale.total_amount || 0));
        }
    });

    const labels = Array.from(map.keys()).map((key) => {
        const date = new Date(`${key}T00:00:00`);
        return new Intl.DateTimeFormat("es-419", { day: "numeric", month: "short" }).format(date);
    });
    const values = Array.from(map.values()).map((value) => Number(value.toFixed(2)));
    return { labels, values };
}

function bucketByWeek(sales, start, end) {
    const weekStarts = [];
    let cursor = startOfDay(start);
    const bound = endOfDay(end);
    while (cursor <= bound) {
        weekStarts.push(cursor);
        cursor = addDays(cursor, 7);
    }

    const totals = new Array(weekStarts.length).fill(0);
    sales.forEach((sale) => {
        const t = new Date(sale.created_at);
        let bucketIndex = 0;
        for (let i = 0; i < weekStarts.length; i += 1) {
            if (weekStarts[i] <= t) {
                bucketIndex = i;
            } else {
                break;
            }
        }
        totals[bucketIndex] += Number(sale.total_amount || 0);
    });

    const shortFmt = new Intl.DateTimeFormat("es-419", { day: "numeric", month: "short" });
    const labels = weekStarts.map((date) => `Sem. ${shortFmt.format(date)}`);
    const values = totals.map((value) => Number(value.toFixed(2)));
    return { labels, values };
}

function bucketByMonth(sales, start, end) {
    const map = new Map();
    let cursor = new Date(start.getFullYear(), start.getMonth(), 1);
    const endCursor = new Date(end.getFullYear(), end.getMonth(), 1);
    while (cursor <= endCursor) {
        map.set(monthKey(cursor), 0);
        cursor = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1);
    }

    sales.forEach((sale) => {
        const key = monthKey(new Date(sale.created_at));
        if (map.has(key)) {
            map.set(key, map.get(key) + Number(sale.total_amount || 0));
        }
    });

    const labels = Array.from(map.keys()).map(monthLabel);
    const values = Array.from(map.values()).map((value) => Number(value.toFixed(2)));
    return { labels, values };
}

function computeDailySeries(entries, range) {
    if (!range.start && !range.end) {
        return buildFixedDailySeries(entries);
    }
    const { start, end } = resolveRangeBounds(range, entries);
    const spanDays = daysBetween(start, end);
    if (spanDays <= 31) {
        return bucketByDay(entries, start, end);
    }
    if (spanDays <= 180) {
        return bucketByWeek(entries, start, end);
    }
    return bucketByMonth(entries, start, end);
}

function computeMonthlySeries(entries, range) {
    if (!range.start && !range.end) {
        return buildFixedMonthlySeries(entries);
    }
    const { start, end } = resolveRangeBounds(range, entries);
    return bucketByMonth(entries, start, end);
}

function buildLowStock(products) {
    return [...products]
        .filter((product) => Number(product.stock_quantity) <= 10)
        .sort((a, b) => a.stock_quantity - b.stock_quantity)
        .slice(0, 5);
}

function updateChartLabels(range, sales, purchases) {
    if (!range.start && !range.end) {
        if (dailyChartLabel) {
            dailyChartLabel.textContent = "Últimos 7 días";
        }
        if (monthlyChartLabel) {
            monthlyChartLabel.textContent = "Últimos 6 meses";
        }
        if (purchasesChartLabel) {
            purchasesChartLabel.textContent = "Últimos 6 meses";
        }
        return;
    }
    const combined = [...sales, ...purchases];
    const { start, end } = resolveRangeBounds(range, combined);
    const shortFmt = new Intl.DateTimeFormat("es-419", { day: "numeric", month: "short" });
    const text = `${shortFmt.format(start)} – ${shortFmt.format(end)}`;
    if (dailyChartLabel) {
        dailyChartLabel.textContent = text;
    }
    if (monthlyChartLabel) {
        monthlyChartLabel.textContent = text;
    }
    if (purchasesChartLabel) {
        purchasesChartLabel.textContent = text;
    }
}

function renderAll() {
    const filteredSales = filterEntriesByRange(rawSales, currentRange);
    const filteredPurchases = filterEntriesByRange(rawPurchases, currentRange);
    const topProducts = buildTopProducts(rawProducts, filteredSales);
    const topSuppliers = buildTopSuppliers(rawSuppliers, filteredPurchases);
    const lowStock = buildLowStock(rawProducts);
    const daily = computeDailySeries(filteredSales, currentRange);
    const monthly = computeMonthlySeries(filteredSales, currentRange);
    const monthlyPurchases = computeMonthlySeries(filteredPurchases, currentRange);
    const totalSales = totalAmount(filteredSales);
    const totalPurchases = totalAmount(filteredPurchases);

    renderTopProducts(topProducts);
    renderLowStock(lowStock);
    renderTopSuppliers(topSuppliers);
    renderDailySalesChart(daily.labels, daily.values);
    renderMonthlyRevenueChart(monthly.labels, monthly.values);
    renderMonthlyPurchasesChart(monthlyPurchases.labels, monthlyPurchases.values);
    renderStats({ totalSales, totalPurchases });
    updateChartLabels(currentRange, filteredSales, filteredPurchases);

    if (filterSummary) {
        filterSummary.textContent = formatRangeSummary(currentRange, filteredSales.length);
    }

    latestReportData = {
        sales: filteredSales,
        purchases: filteredPurchases,
        suppliers: rawSuppliers,
        topProducts,
        topSuppliers,
        lowStock,
        totalSales,
        totalPurchases,
        businessName,
        rangeLabel: formatRangeLabel(currentRange),
    };

    if (exportButton) {
        exportButton.disabled = false;
    }
    if (exportPdfButton) {
        exportPdfButton.disabled = false;
    }
}

async function initReports() {
    try {
        const [products, sales, purchases, suppliers, settings] = await Promise.all([
            fetchProductsForReports(),
            fetchSalesForReports(),
            fetchPurchasesForReports(),
            fetchSuppliersForReports(),
            fetchAppSettings().catch(() => null),
        ]);

        rawProducts = products;
        rawSales = sales;
        rawPurchases = purchases;
        rawSuppliers = suppliers;
        businessName = settings?.business_name || "Hamster";

        renderAll();
    } catch (error) {
        if (error instanceof ApiError) {
            showReportsError(error.message);
            return;
        }
        showReportsError("No se pudieron cargar los datos de reportes.");
    }
}

function handlePresetChange() {
    const preset = presetSelect?.value || "all";
    if (preset === "custom") {
        return;
    }
    const range = computePresetRange(preset);
    currentRange = range;
    if (startInput) {
        startInput.value = toDatetimeLocalValue(range.start);
    }
    if (endInput) {
        endInput.value = toDatetimeLocalValue(range.end);
    }
    renderAll();
}

function handleCustomInputChange() {
    if (presetSelect) {
        presetSelect.value = "custom";
    }
    currentRange = {
        start: parseDatetimeLocalValue(startInput?.value),
        end: parseDatetimeLocalValue(endInput?.value),
    };
    renderAll();
}

function handleClearFilter() {
    if (presetSelect) {
        presetSelect.value = "all";
    }
    if (startInput) {
        startInput.value = "";
    }
    if (endInput) {
        endInput.value = "";
    }
    currentRange = { start: null, end: null };
    renderAll();
}

function handleExportClick() {
    if (!latestReportData) {
        return;
    }
    const csv = buildReportsCsv(latestReportData);
    const stamp = new Date().toISOString().slice(0, 10);
    const slug = latestReportData.businessName.toLowerCase().replace(/\s+/g, "-");
    downloadCsv(`reporte-${slug}-${stamp}.csv`, csv);
    notify("success", "Reporte exportado en CSV.");
}

function handleExportPdfClick() {
    if (!latestReportData) {
        return;
    }
    try {
        buildAndDownloadReportsPdf(latestReportData);
        notify("success", "Reporte exportado en PDF.");
    } catch (error) {
        notify("error", error.message || "No se pudo generar el PDF.");
    }
}

presetSelect?.addEventListener("change", handlePresetChange);
startInput?.addEventListener("change", handleCustomInputChange);
endInput?.addEventListener("change", handleCustomInputChange);
clearButton?.addEventListener("click", handleClearFilter);
exportButton?.addEventListener("click", handleExportClick);
exportPdfButton?.addEventListener("click", handleExportPdfClick);

initReports();
