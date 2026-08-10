function currency(value) {
    const amount = Number(value);
    if (Number.isNaN(amount)) {
        return "$0.00";
    }
    return new Intl.NumberFormat("es-419", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 2,
    }).format(amount);
}

function hideLoading(loadingId, targetId) {
    const loading = document.getElementById(loadingId);
    const target = document.getElementById(targetId);
    loading?.classList.add("hidden");
    target?.classList.remove("hidden");
}

function showEmpty(loadingId, emptyId) {
    const loading = document.getElementById(loadingId);
    const empty = document.getElementById(emptyId);
    loading?.classList.add("hidden");
    empty?.classList.remove("hidden");
}

export function renderTopProducts(items) {
    const list = document.getElementById("reports-top-products-list");
    if (!list) {
        return;
    }

    if (!items.length) {
        showEmpty("reports-top-products-loading", "reports-top-products-empty");
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

    hideLoading("reports-top-products-loading", "reports-top-products-list");
}

export function renderLowStock(items) {
    const list = document.getElementById("reports-low-stock-list");
    if (!list) {
        return;
    }

    if (!items.length) {
        showEmpty("reports-low-stock-loading", "reports-low-stock-empty");
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

    hideLoading("reports-low-stock-loading", "reports-low-stock-list");
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

export function renderDailySalesChart(labels, values) {
    const canvas = document.getElementById("reports-daily-chart");
    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    hideLoading("reports-daily-chart-loading", "reports-daily-chart");

    new Chart(canvas, {
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

    hideLoading("reports-monthly-chart-loading", "reports-monthly-chart");

    new Chart(canvas, {
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

export function showReportsError(message) {
    const errorBox = document.getElementById("reports-error");
    if (!errorBox) {
        return;
    }
    errorBox.textContent = message;
    errorBox.classList.remove("hidden");
}
