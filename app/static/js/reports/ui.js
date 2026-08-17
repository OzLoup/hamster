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

function hideLoading(loadingId, targetId) {
    document.getElementById(loadingId)?.classList.add("hidden");
    document.getElementById(targetId)?.classList.remove("hidden");
}

function setSectionState(loadingId, contentId, emptyId, state) {
    document.getElementById(loadingId)?.classList.toggle("hidden", state !== "loading");
    document.getElementById(contentId)?.classList.toggle("hidden", state !== "content");
    document.getElementById(emptyId)?.classList.toggle("hidden", state !== "empty");
}

export function renderTopProducts(items) {
    const list = document.getElementById("reports-top-products-list");
    if (!list) {
        return;
    }

    if (!items.length) {
        list.innerHTML = "";
        setSectionState("reports-top-products-loading", "reports-top-products-list", "reports-top-products-empty", "empty");
        return;
    }

    list.innerHTML = items
        .map(
            (item, index) => `
                <div class="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/65 px-3 py-2.5">
                    <div class="flex items-center gap-3">
                        <span class="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-brand-500/20 text-xs font-semibold text-brand-200">${index + 1}</span>
                        <div>
                            <p class="text-sm font-medium text-slate-100">${item.name}</p>
                            <p class="text-xs text-slate-400">Cant. vendida: ${item.quantity}</p>
                        </div>
                    </div>
                    <span class="text-xs text-emerald-300">${currency(item.revenue)}</span>
                </div>
            `
        )
        .join("");

    setSectionState("reports-top-products-loading", "reports-top-products-list", "reports-top-products-empty", "content");
}

export function renderLowStock(items) {
    const list = document.getElementById("reports-low-stock-list");
    if (!list) {
        return;
    }

    if (!items.length) {
        list.innerHTML = "";
        setSectionState("reports-low-stock-loading", "reports-low-stock-list", "reports-low-stock-empty", "empty");
        return;
    }

    list.innerHTML = items
        .map(
            (item) => `
                <div class="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/65 px-3 py-2.5">
                    <p class="text-sm font-medium text-slate-100">${item.name}</p>
                    <span class="rounded-lg bg-rose-500/20 px-2 py-1 text-xs text-rose-200">Stock disponible: ${item.stock_quantity}</span>
                </div>
            `
        )
        .join("");

    setSectionState("reports-low-stock-loading", "reports-low-stock-list", "reports-low-stock-empty", "content");
}

export function renderTopSuppliers(items) {
    const list = document.getElementById("reports-top-suppliers-list");
    if (!list) {
        return;
    }

    if (!items.length) {
        list.innerHTML = "";
        setSectionState("reports-top-suppliers-loading", "reports-top-suppliers-list", "reports-top-suppliers-empty", "empty");
        return;
    }

    list.innerHTML = items
        .map(
            (item, index) => `
                <div class="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/65 px-3 py-2.5">
                    <div class="flex items-center gap-3">
                        <span class="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-amber-500/20 text-xs font-semibold text-amber-200">${index + 1}</span>
                        <div>
                            <p class="text-sm font-medium text-slate-100">${item.name}</p>
                            <p class="text-xs text-slate-400">Compras: ${item.count}</p>
                        </div>
                    </div>
                    <span class="text-xs text-rose-300">${currency(item.amount)}</span>
                </div>
            `
        )
        .join("");

    setSectionState("reports-top-suppliers-loading", "reports-top-suppliers-list", "reports-top-suppliers-empty", "content");
}

export function renderPaymentBreakdown(breakdown) {
    const wrap = document.getElementById("reports-payment-breakdown-wrap");
    if (!wrap) {
        return;
    }

    wrap.innerHTML = `
        <table class="min-w-full text-left text-sm">
            <thead>
                <tr class="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-400">
                    <th class="px-3 py-2 font-medium">Método de pago</th>
                    <th class="px-3 py-2 font-medium">Cant. de ventas</th>
                    <th class="px-3 py-2 font-medium text-right">Subtotal</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-800">
                ${breakdown.rows
                    .map(
                        (row) => `
                            <tr>
                                <td class="px-3 py-2.5 text-slate-200">${row.label}</td>
                                <td class="px-3 py-2.5 text-slate-400">${row.count}</td>
                                <td class="px-3 py-2.5 text-right text-slate-100">${currency(row.amount)}</td>
                            </tr>
                        `
                    )
                    .join("")}
            </tbody>
            <tfoot>
                <tr class="border-t border-slate-700 font-semibold">
                    <td class="px-3 py-3 text-slate-100">Total</td>
                    <td class="px-3 py-3 text-slate-300">${breakdown.totalCount}</td>
                    <td class="px-3 py-3 text-right text-emerald-300">${currency(breakdown.totalAmount)}</td>
                </tr>
            </tfoot>
        </table>
    `;

    hideLoading("reports-payment-breakdown-loading", "reports-payment-breakdown-wrap");
}

export function renderStats({ totalSales, totalPurchases }) {
    const salesEl = document.getElementById("reports-stat-sales");
    const purchasesEl = document.getElementById("reports-stat-purchases");
    const balanceEl = document.getElementById("reports-stat-balance");
    const balance = Number(totalSales || 0) - Number(totalPurchases || 0);

    if (salesEl) {
        salesEl.textContent = currency(totalSales);
    }
    if (purchasesEl) {
        purchasesEl.textContent = currency(totalPurchases);
    }
    if (balanceEl) {
        balanceEl.textContent = currency(balance);
        balanceEl.classList.toggle("text-emerald-300", balance >= 0);
        balanceEl.classList.toggle("text-rose-300", balance < 0);
        balanceEl.classList.toggle("text-slate-100", false);
    }
}

function chartDatasetStyle(baseColor) {
    return {
        borderColor: baseColor,
        backgroundColor: `${baseColor}33`,
        pointBackgroundColor: baseColor,
        pointRadius: 3,
        tension: 0.35,
        fill: true,
    };
}

let dailyChartInstance = null;
let monthlyChartInstance = null;
let purchasesChartInstance = null;

export function renderDailySalesChart(labels, values) {
    const canvas = document.getElementById("reports-daily-chart");
    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    hideLoading("reports-daily-chart-loading", "reports-daily-chart-wrap");

    dailyChartInstance?.destroy();
    dailyChartInstance = new Chart(canvas, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "Ventas diarias",
                    data: values,
                    ...chartDatasetStyle("#22d3ee"),
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: "#cbd5e1",
                    },
                },
            },
            scales: {
                x: {
                    ticks: {
                        color: "#94a3b8",
                    },
                    grid: {
                        color: "#1e293b",
                    },
                },
                y: {
                    ticks: {
                        color: "#94a3b8",
                    },
                    grid: {
                        color: "#1e293b",
                    },
                },
            },
        },
    });
}

export function renderMonthlyRevenueChart(labels, values) {
    const canvas = document.getElementById("reports-monthly-chart");
    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    hideLoading("reports-monthly-chart-loading", "reports-monthly-chart-wrap");

    monthlyChartInstance?.destroy();
    monthlyChartInstance = new Chart(canvas, {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    label: "Ingresos mensuales",
                    data: values,
                    borderRadius: 8,
                    backgroundColor: "#3b82f6aa",
                    borderColor: "#60a5fa",
                    borderWidth: 1,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: "#cbd5e1",
                    },
                },
            },
            scales: {
                x: {
                    ticks: {
                        color: "#94a3b8",
                    },
                    grid: {
                        color: "#1e293b",
                    },
                },
                y: {
                    ticks: {
                        color: "#94a3b8",
                    },
                    grid: {
                        color: "#1e293b",
                    },
                },
            },
        },
    });
}

export function renderMonthlyPurchasesChart(labels, values) {
    const canvas = document.getElementById("reports-purchases-chart");
    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    hideLoading("reports-purchases-chart-loading", "reports-purchases-chart-wrap");

    purchasesChartInstance?.destroy();
    purchasesChartInstance = new Chart(canvas, {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    label: "Compras mensuales",
                    data: values,
                    borderRadius: 8,
                    backgroundColor: "#fb7185aa",
                    borderColor: "#fda4af",
                    borderWidth: 1,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: "#cbd5e1",
                    },
                },
            },
            scales: {
                x: {
                    ticks: {
                        color: "#94a3b8",
                    },
                    grid: {
                        color: "#1e293b",
                    },
                },
                y: {
                    ticks: {
                        color: "#94a3b8",
                    },
                    grid: {
                        color: "#1e293b",
                    },
                },
            },
        },
    });
}

export function showReportsError(message) {
    const errorBox = document.getElementById("reports-error");
    if (!errorBox) {
        return;
    }
    errorBox.textContent = message;
    errorBox.classList.remove("hidden");
}
