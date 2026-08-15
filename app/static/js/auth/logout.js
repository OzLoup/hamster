import { logout } from "./api.js";

document.getElementById("logout-button")?.addEventListener("click", async () => {
    try {
        await logout();
    } finally {
        window.location.href = "/login";
    }
});
