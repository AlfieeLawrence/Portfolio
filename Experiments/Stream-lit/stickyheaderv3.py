import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

# -----------------------------------------------------------------------------
# Theme-aware sticky banner (CSS variables driven by JS)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
/* ------------------------------------------------------------------
   Theme variables (defaults = light)
------------------------------------------------------------------ */
:root {
    --banner-bg: #ffffff;
    --banner-border: rgba(0,0,0,0.1);
}

/* ------------------------------------------------------------------
   Remove Streamlit's default top padding
------------------------------------------------------------------ */
.block-container {
    padding-top: 0rem !important;
}

/* ------------------------------------------------------------------
   Sticky banner container
------------------------------------------------------------------ */
div[data-testid="stVerticalBlock"]
> div:has(div.sticky-banner-marker) {
    position: sticky;
    top: 0;
    z-index: 1000;

    background-color: var(--banner-bg);
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--banner-border);
}

/* Marker element (zero height) */
.sticky-banner-marker {
    height: 0;
}
</style>

<script>
/* ------------------------------------------------------------------
   Get Streamlit theme (body or html, depending on version)
------------------------------------------------------------------ */
function getTheme() {
    return (
        document.body.getAttribute("data-theme") ||
        document.documentElement.getAttribute("data-theme")
    );
}

/* ------------------------------------------------------------------
   Apply theme → CSS variables
------------------------------------------------------------------ */
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

/* Initial run (after DOM settles) */
setTimeout(applyThemeVars, 0);

/* React to Streamlit theme changes */
const observer = new MutationObserver(applyThemeVars);
observer.observe(document.documentElement, { attributes: true });
observer.observe(document.body, { attributes: true });
</script>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Sticky banner contents
# -----------------------------------------------------------------------------
banner = st.container()
banner.markdown(
    "<div class='sticky-banner-marker'></div>",
    unsafe_allow_html=True
)

col1, col2, col3 = banner.columns(3)

with col1:
    st.selectbox("Category", ["All", "A", "B", "C"])

with col2:
    st.text_input("Search")

with col3:
    st.button("Apply")

# -----------------------------------------------------------------------------
# Scrollable content (for testing)
# -----------------------------------------------------------------------------
df = pd.DataFrame({
    "Item": [f"Item {i}" for i in range(300)],
    "Value": range(300),
})

st.dataframe(df, height=600)