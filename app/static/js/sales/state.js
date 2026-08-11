export function createSalesState() {
    return {
        products: [],
        productsById: new Map(),
        lines: [],
        paymentMethod: "",
    };
}
