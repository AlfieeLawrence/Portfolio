import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

# --------------------------------------------------
# Theme-aware colors
# --------------------------------------------------
theme_base = st.get_option("theme.base")

if theme_base == "dark":
    banner_bg = "#000000"
    border_color = "rgba(255,255,255,0.15)"
else:
    banner_bg = "#ffffff"
    border_color = "rgba(0,0,0,0.1)"

# --------------------------------------------------
# CSS
# --------------------------------------------------
st.markdown(f"""
<style>

/* Remove Streamlit top gap */
.block-container {{
    padding-top: 0rem !important;
}}

/* Sticky banner */
div[data-testid="stVerticalBlock"]
> div:has(div.sticky-banner-marker) {{
    position: sticky;
    top: 0;
    z-index: 1000;

    background-color: {banner_bg};
    padding: 1rem 1.25rem;

    border-bottom: 1px solid {border_color};
}}

/* Marker */
.sticky-banner-marker {{
    height: 0;
}}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Sticky banner content
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