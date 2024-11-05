// Check if the URL contains a search query to determine if we should scroll
window.onload = function () {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has("search")) {
        // Scroll to the iframe if search query is present
        document.getElementById("map-frame").scrollIntoView({ behavior: "smooth" });
    }
};
