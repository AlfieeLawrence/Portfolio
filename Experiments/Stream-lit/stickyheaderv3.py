import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="Sticky Box Demo")

# --------------------------------------------------
# Sticky box CSS (simple + correct)
# --------------------------------------------------
st.markdown("""
<style>
/* Sticky wrapper */
div[data-testid="stVerticalBlock"]
> div:has(div.sticky-box-marker) {
    position: sticky;
    top: 0;
    z-index: 1000;
}

/* Actual box */
div[data-testid="stVerticalBlock"]
> div:has(div.sticky-box-marker)
> div {
    background-color: var(--background-color);
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--sidebar-border-color);
}
            
/* Marker */
.sticky-box-marker {
    height: 0;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Sticky box (you put anything inside this)
# --------------------------------------------------
sticky = st.container()
sticky.markdown("<div class='sticky-box-marker'></div>", unsafe_allow_html=True)

col1, col2, col3 = sticky.columns(3)

with col1:
    st.selectbox("Category", ["All", "A", "B", "C"])

with col2:
    st.text_input("Search")

with col3:
    st.button("Apply")

# --------------------------------------------------
# Below is just scroll content to prove behavior
# --------------------------------------------------
df = pd.DataFrame({
    "Item": [f"Item {i}" for i in range(200)],
    "Value": range(200),
})

st.dataframe(df, height=600)