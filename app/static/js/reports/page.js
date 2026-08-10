import { ApiError, fetchProductsForReports, fetchSalesForReports } from "./api.js";
import {
    renderDailySalesChart,
    renderLowStock,
    renderMonthlyRevenueChart,
    renderTopProducts,
    showReportsError,
} from "./ui.js";

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

function buildDailySalesSeries(sales) {
    const map = new Map();
    const today = new Date();

    for (let i = 6; i >= 0; i -= 1) {
        const date = new Date(today);
        date.setDate(today.getDate() - i);
        map.set(isoDate(date), 0);
    }

    sales.forEach((sale) => {
        const key = isoDate(new Date(sale.created_at));
        if (!map.has(key)) {
            return;
        }
        map.set(key, map.get(key) + Number(sale.total_amount || 0));
    });

    const labels = Array.from(map.keys()).map((key) => {
        const date = new Date(key);
        return new Intl.DateTimeFormat("es-419", { weekday: "short" }).format(date);
    });
    const values = Array.from(map.values()).map((value) => Number(value.toFixed(2)));

    return { labels, values };
}

function buildMonthlyRevenueSeries(sales) {
    const map = new Map();
    const now = new Date();

    for (let i = 5; i >= 0; i -= 1) {
        const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
        map.set(monthKey(date), 0);
    }

    sales.forEach((sale) => {
        const key = monthKey(new Date(sale.created_at));
        if (!map.has(key)) {
            return;
        }
        map.set(key, map.get(key) + Number(sale.total_amount || 0));
    });

    const labels = Array.from(map.keys()).map(monthLabel);
    const values = Array.from(map.values()).map((value) => Number(value.toFixed(2)));

    return { labels, values };
}

function buildLowStock(products) {
    return [...products]
        .filter((product) => Number(product.stock_quantity) <= 10)
        .sort((a, b) => a.stock_quantity - b.stock_quantity)
        .slice(0, 5);
}

async function initReports() {
    try {
        const [products, sales] = await Promise.all([fetchProductsForReports(), fetchSalesForReports()]);

        const topProducts = buildTopProducts(products, sales);
        const lowStock = buildLowStock(products);
        const daily = buildDailySalesSeries(sales);
        const monthly = buildMonthlyRevenueSeries(sales);

        renderTopProducts(topProducts);
        renderLowStock(lowStock);
        renderDailySalesChart(daily.labels, daily.values);
        renderMonthlyRevenueChart(monthly.labels, monthly.values);
    } catch (error) {
        if (error instanceof ApiError) {
            showReportsError(error.message);
            return;
        }
        showReportsError("No se pudieron cargar los datos de reportes.");
    }
}

initReports();
