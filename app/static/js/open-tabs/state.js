export function createOpenTabsState() {
    return {
        tabs: [],
        tabsById: new Map(),
        products: [],
        productsById: new Map(),
        activeTabId: null,
    };
}
