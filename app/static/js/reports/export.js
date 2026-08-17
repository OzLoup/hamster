const PAYMENT_METHOD_LABELS = {
    cash: "Efectivo",
    card: "Tarjeta",
    nequi: "Nequi",
    daviplata: "Daviplata",
    bre_b: "Bre-B",
};

const ROLE_LABELS = {
    admin: "Administrador",
    coordinator: "Coordinador",
    seller: "Vendedor",
};

function escapeCsvField(value) {
    const str = String(value ?? "");
    if (/[",\n]/.test(str)) {
        return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
}

function toCsvRow(fields) {
    return fields.map(escapeCsvField).join(",");
}

function decimalValue(value) {
    return Number(value || 0).toFixed(2);
}

function formatCop(value) {
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

function totalAmount(entries) {
    return entries.reduce((sum, entry) => sum + Number(entry.total_amount || 0), 0);
}

function sortedByDate(entries) {
    return [...entries].sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
}

function supplierNameMap(suppliers) {
    return new Map((suppliers || []).map((supplier) => [supplier.id, supplier.name]));
}

export function buildReportsCsv({
    sales,
    purchases,
    suppliers,
    topProducts,
    topSuppliers,
    lowStock,
    paymentBreakdown,
    rangeLabel,
    role,
}) {
    const canSeeFinancials = role === "admin" || role === "coordinator";
    const canSeeBalance = role === "admin";
    const lines = [];
    const totalSales = totalAmount(sales);
    const totalPurchases = totalAmount(purchases);
    const balance = totalSales - totalPurchases;
    const supplierNames = supplierNameMap(suppliers);

    lines.push(`Reporte de ventas${canSeeFinancials ? " y compras" : ""} - Hamster`);
    lines.push(toCsvRow(["Generado", new Date().toLocaleString("es-CO")]));
    lines.push(toCsvRow(["Periodo", rangeLabel || "Todo el tiempo"]));
    if (role && role !== "admin") {
        lines.push(toCsvRow(["Alcance", `Vista ${ROLE_LABELS[role] || role}`]));
    }
    lines.push("");

    lines.push("RESUMEN");
    lines.push(toCsvRow(["Total ventas", decimalValue(totalSales)]));
    if (canSeeFinancials) {
        lines.push(toCsvRow(["Total compras", decimalValue(totalPurchases)]));
    }
    if (canSeeBalance) {
        lines.push(toCsvRow(["Balance", decimalValue(balance)]));
    }
    lines.push("");

    lines.push("VENTAS POR METODO DE PAGO");
    lines.push(toCsvRow(["Metodo de pago", "Cantidad de ventas", "Subtotal"]));
    paymentBreakdown.rows.forEach((row) => {
        lines.push(toCsvRow([row.label, row.count, decimalValue(row.amount)]));
    });
    lines.push(toCsvRow(["Total", paymentBreakdown.totalCount, decimalValue(paymentBreakdown.totalAmount)]));
    lines.push("");

    lines.push("VENTAS");
    lines.push(toCsvRow(["Fecha", "Referencia", "Metodo de pago", "Total"]));
    sortedByDate(sales).forEach((sale) => {
        lines.push(
            toCsvRow([
                new Date(sale.created_at).toLocaleString("es-CO"),
                sale.reference,
                PAYMENT_METHOD_LABELS[sale.payment_method] || sale.payment_method,
                decimalValue(sale.total_amount),
            ])
        );
    });
    lines.push(toCsvRow(["", "", "Total de ventas", decimalValue(totalSales)]));

    if (canSeeFinancials) {
        lines.push("");
        lines.push("COMPRAS");
        lines.push(toCsvRow(["Fecha", "Referencia", "Proveedor", "Total"]));
        sortedByDate(purchases).forEach((purchase) => {
            lines.push(
                toCsvRow([
                    new Date(purchase.created_at).toLocaleString("es-CO"),
                    purchase.reference,
                    supplierNames.get(purchase.supplier_id) || `Proveedor #${purchase.supplier_id}`,
                    decimalValue(purchase.total_amount),
                ])
            );
        });
        lines.push(toCsvRow(["", "", "Total de compras", decimalValue(totalPurchases)]));
    }

    if (role === "admin") {
        lines.push("");
        lines.push("PRODUCTOS MAS VENDIDOS");
        lines.push(toCsvRow(["Producto", "Cantidad vendida", "Ingresos"]));
        topProducts.forEach((product) => {
            lines.push(toCsvRow([product.name, product.quantity, decimalValue(product.revenue)]));
        });
    }

    if (canSeeFinancials) {
        lines.push("");
        lines.push("COMPRAS POR PROVEEDOR");
        lines.push(toCsvRow(["Proveedor", "Cantidad de compras", "Total"]));
        topSuppliers.forEach((supplier) => {
            lines.push(toCsvRow([supplier.name, supplier.count, decimalValue(supplier.amount)]));
        });

        lines.push("");
        lines.push("PRODUCTOS CON BAJO STOCK");
        lines.push(toCsvRow(["Producto", "SKU", "Stock actual"]));
        lowStock.forEach((product) => {
            lines.push(toCsvRow([product.name, product.sku, product.stock_quantity]));
        });
    }

    return lines.join("\n");
}

export function downloadCsv(filename, content) {
    const blob = new Blob([`﻿${content}`], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

export function buildAndDownloadReportsPdf({
    sales,
    purchases,
    suppliers,
    topProducts,
    topSuppliers,
    lowStock,
    paymentBreakdown,
    businessName,
    rangeLabel,
    role,
}) {
    const JsPdfCtor = window.jspdf?.jsPDF;
    if (!JsPdfCtor) {
        throw new Error("No se pudo cargar el generador de PDF.");
    }

    const canSeeFinancials = role === "admin" || role === "coordinator";
    const canSeeBalance = role === "admin";

    const doc = new JsPdfCtor({ unit: "pt", format: "a4" });
    const marginX = 40;
    const pageWidth = doc.internal.pageSize.getWidth();
    const totalSales = totalAmount(sales);
    const totalPurchases = totalAmount(purchases);
    const balance = totalSales - totalPurchases;
    const supplierNames = supplierNameMap(suppliers);

    doc.setFont("helvetica", "bold");
    doc.setFontSize(18);
    doc.setTextColor(20, 20, 20);
    doc.text(businessName || "Hamster", marginX, 50);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(11);
    doc.setTextColor(90, 90, 90);
    doc.text(`Reporte de ventas${canSeeFinancials ? " y compras" : ""}`, marginX, 68);
    doc.text(`Generado: ${new Date().toLocaleString("es-CO")}`, marginX, 84);
    doc.text(`Periodo: ${rangeLabel || "Todo el tiempo"}`, marginX, 100);
    let headerY = 100;
    if (role && role !== "admin") {
        headerY = 116;
        doc.text(`Alcance: Vista ${ROLE_LABELS[role] || role}`, marginX, headerY);
    }

    doc.setFont("helvetica", "bold");
    doc.setFontSize(10);
    doc.setTextColor(15, 118, 110);
    doc.text(`Total ventas: ${formatCop(totalSales)}`, marginX, headerY + 18);
    if (canSeeFinancials) {
        doc.setTextColor(190, 18, 60);
        doc.text(`Total compras: ${formatCop(totalPurchases)}`, marginX + 180, headerY + 18);
    }
    if (canSeeBalance) {
        doc.setTextColor(balance >= 0 ? 5 : 190, balance >= 0 ? 150 : 18, balance >= 0 ? 105 : 60);
        doc.text(`Balance: ${formatCop(balance)}`, marginX + 360, headerY + 18);
    }

    doc.setDrawColor(220, 220, 220);
    doc.line(marginX, headerY + 30, pageWidth - marginX, headerY + 30);

    doc.autoTable({
        startY: headerY + 46,
        margin: { left: marginX, right: marginX },
        head: [["Método de pago", "Cant. de ventas", "Subtotal"]],
        body: paymentBreakdown.rows.map((row) => [row.label, String(row.count), formatCop(row.amount)]),
        foot: [["Total", String(paymentBreakdown.totalCount), formatCop(paymentBreakdown.totalAmount)]],
        headStyles: { fillColor: [8, 145, 178] },
        footStyles: { fillColor: [241, 245, 249], textColor: [15, 23, 42], fontStyle: "bold" },
        styles: { fontSize: 9, cellPadding: 5 },
        columnStyles: { 2: { halign: "right" } },
    });

    doc.autoTable({
        startY: doc.lastAutoTable.finalY + 24,
        margin: { left: marginX, right: marginX },
        head: [["Fecha", "Referencia", "Método de pago", "Total"]],
        body: sortedByDate(sales).map((sale) => [
            new Date(sale.created_at).toLocaleString("es-CO"),
            sale.reference,
            PAYMENT_METHOD_LABELS[sale.payment_method] || sale.payment_method,
            formatCop(sale.total_amount),
        ]),
        foot: [["", "", "Total de ventas", formatCop(totalSales)]],
        headStyles: { fillColor: [15, 118, 110] },
        footStyles: { fillColor: [241, 245, 249], textColor: [15, 23, 42], fontStyle: "bold" },
        styles: { fontSize: 9, cellPadding: 5 },
        columnStyles: { 3: { halign: "right" } },
    });

    if (canSeeFinancials) {
        doc.autoTable({
            startY: doc.lastAutoTable.finalY + 24,
            margin: { left: marginX, right: marginX },
            head: [["Fecha", "Referencia", "Proveedor", "Total"]],
            body: sortedByDate(purchases).map((purchase) => [
                new Date(purchase.created_at).toLocaleString("es-CO"),
                purchase.reference,
                supplierNames.get(purchase.supplier_id) || `Proveedor #${purchase.supplier_id}`,
                formatCop(purchase.total_amount),
            ]),
            foot: [["", "", "Total de compras", formatCop(totalPurchases)]],
            headStyles: { fillColor: [190, 18, 60] },
            footStyles: { fillColor: [241, 245, 249], textColor: [15, 23, 42], fontStyle: "bold" },
            styles: { fontSize: 9, cellPadding: 5 },
            columnStyles: { 3: { halign: "right" } },
        });
    }

    if (role === "admin") {
        doc.autoTable({
            startY: doc.lastAutoTable.finalY + 24,
            margin: { left: marginX, right: marginX },
            head: [["Productos más vendidos", "Cantidad vendida", "Ingresos"]],
            body: topProducts.map((product) => [product.name, String(product.quantity), formatCop(product.revenue)]),
            headStyles: { fillColor: [15, 118, 110] },
            styles: { fontSize: 9, cellPadding: 5 },
            columnStyles: { 2: { halign: "right" } },
        });
    }

    if (canSeeFinancials) {
        doc.autoTable({
            startY: doc.lastAutoTable.finalY + 24,
            margin: { left: marginX, right: marginX },
            head: [["Compras por proveedor", "Cantidad de compras", "Total"]],
            body: topSuppliers.map((supplier) => [supplier.name, String(supplier.count), formatCop(supplier.amount)]),
            headStyles: { fillColor: [190, 18, 60] },
            styles: { fontSize: 9, cellPadding: 5 },
            columnStyles: { 2: { halign: "right" } },
        });

        doc.autoTable({
            startY: doc.lastAutoTable.finalY + 24,
            margin: { left: marginX, right: marginX },
            head: [["Productos con bajo stock", "SKU", "Stock actual"]],
            body: lowStock.map((product) => [product.name, product.sku, String(product.stock_quantity)]),
            headStyles: { fillColor: [180, 130, 20] },
            styles: { fontSize: 9, cellPadding: 5 },
            columnStyles: { 2: { halign: "right" } },
        });
    }

    const stamp = new Date().toISOString().slice(0, 10);
    const roleSuffix = role && role !== "admin" ? `-${role}` : "";
    doc.save(`reporte-${(businessName || "hamster").toLowerCase().replace(/\s+/g, "-")}${roleSuffix}-${stamp}.pdf`);
}
