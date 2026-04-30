st.markdown("""
<style>
:root {
    --banner-bg: #ffffff;
    --banner-border: rgba(0,0,0,0.1);
}

/* Remove Streamlit top gap */
.block-container {
    padding-top: 0rem !important;
}

/* Sticky banner */
div[data-testid="stVerticalBlock"]
> div:has(div.sticky-banner-marker) {
    position: sticky;
    top: 0;
    z-index: 1000;

    background-color: var(--banner-bg);
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--banner-border);
}

/* Marker */
.sticky-banner-marker {
    height: 0;
}
</style>

<script>
function getTheme() {
    // Streamlit may attach data-theme to BODY or HTML depending on version
    return (
        document.body.getAttribute("data-theme") ||
        document.documentElement.getAttribute("data-theme")
    );
}

function applyThemeVars() {
    const theme = getTheme();

    if (theme === "dark") {
        document.documentElement.style.setProperty("--banner-bg", "#000000");
        document.documentElement.style.setProperty(
            "--banner-border",
            "rgba(255,255,255,0.15)"
        );
    } else {
        document.documentElement.style.setProperty("--banner-bg", "#ffffff");
        document.documentElement.style.setProperty(
            "--banner-border",
            "rgba(0,0,0,0.1)"
        );
    }
}

// Run once after DOM settle
setTimeout(applyThemeVars, 0);

// Watch BOTH html and body — Streamlit mutates either
const observer = new MutationObserver(applyThemeVars);
observer.observe(document.documentElement, { attributes: true });
observer.observe(document.body, { attributes: true });
</script>
""", unsafe_allow_html=True)