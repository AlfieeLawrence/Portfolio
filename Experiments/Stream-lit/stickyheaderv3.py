import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.markdown("""
<style>

/* ------------------------------------------------------------------
   Hard-stop transparency issues in Streamlit
------------------------------------------------------------------ */

/* Remove Streamlit top padding */
.block-container {
    padding-top: 0rem !important;
}

/* Sticky banner wrapper */
div[data-testid="stVerticalBlock"]
> div:has(div.sticky-banner-marker) {

    position: sticky;
    top: 0;
    z-index: 1000;

    /* ✅ FORCE OPAQUE BACKGROUND */
    background-color: rgb(255, 255, 255);

    /* ✅ PREVENT LAYER BLEED */
    opacity: 1;
    isolation: isolate;

    padding: 1rem 1.25rem;
    border-bottom: 1px solid rgba(0,0,0,0.12);
}

/* Dark theme override */
@media (prefers-color-scheme: dark) {
  div[data-testid="stVerticalBlock"]
  > div:has(div.sticky-banner-marker) {
      background-color: rgb(0, 0, 0);
      border-bottom: 1px solid rgba(255,255,255,0.15);
  }
}

/* Marker */
.sticky-banner-marker {
    height: 0;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Sticky banner
# --------------------------------------------------
banner = st.container()
banner.markdown("<div class='sticky-banner-marker'></div>", unsafe_allow_html=True)

col1, col2, col3 = banner.columns(3)

with col1:
    st.selectbox("Category", ["All", "A", "B", "C"])

with col2:
    st.text_input("Search")

with col3:
    st.button("Apply")

# --------------------------------------------------
# Scroll content
# --------------------------------------------------
df = pd.DataFrame({
    "Item": [f"Item {i}" for i in range(300)],
    "Value": range(300),
})

st.dataframe(df, height=600)