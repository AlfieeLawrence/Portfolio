import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

# --------------------------------------------------
# CSS: Correct solid sticky box
# --------------------------------------------------
st.markdown("""
<style>
/* Sticky wrapper */
div[data-testid="stVerticalBlock"]
> div:has(div.sticky-marker) {
    position: sticky;
    top: 0;
    z-index: 1000;
}

/* Solid background layer (THIS stops bleed-through) */
div[data-testid="stVerticalBlock"]
> div:has(div.sticky-marker)
::before {
    content: "";
    position: absolute;
    inset: 0;
    background-color: var(--background-color);
    z-index: -1;
}

/* Content container */
div[data-testid="stVerticalBlock"]
> div:has(div.sticky-marker) {
    position: sticky;
    background-color: var(--background-color);
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--sidebar-border-color);
}

/* Marker */
.sticky-marker {
    height: 0;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Sticky box
# --------------------------------------------------
sticky = st.container()
sticky.markdown("<div class='sticky-marker'></div>", unsafe_allow_html=True)

col1, col2, col3 = sticky.columns(3)

with col1:
    st.selectbox("Category", ["All", "A", "B", "C"])

with col2:
    st.text_input("Search")

with col3:
    st.button("Apply")

# --------------------------------------------------
# Scroll content (to prove solidity)
# --------------------------------------------------
df = pd.DataFrame({
    "Item": [f"Item {i}" for i in range(300)],
    "Value": range(300),
})

st.dataframe(df, height=600)