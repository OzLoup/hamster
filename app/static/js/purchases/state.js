export function createPurchasesState() {
    return {
        products: [],
        productsById: new Map(),
        suppliers: [],
        lines: [],
    };
}
