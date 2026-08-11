export function createProductsState() {
    return {
        page: 1,
        pageSize: 10,
        total: 0,
        totalPages: 1,
        search: "",
        categoryId: "",
        stockLevel: "",
        isActive: "",
        sortBy: "",
        sortDir: "asc",
    };
}
