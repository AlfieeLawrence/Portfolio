import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sticky Filters + Sidebar", layout="wide")

# ----------------------------------------------------
# Sticky header styling (no gaps + dark background)
# ----------------------------------------------------
st.markdown("""
<style>

    /* Sticky main filter bar */
    div[data-testid="stVerticalBlock"] div:has(div.fixed-header-marker) {
        position: sticky;
        top: 0;
        z-index: 9999;
        padding-top: 8px;
        padding-bottom: 8px;

        /* Dark translucent background */
        background: rgba(0, 0, 0, 0.70);
        backdrop-filter: blur(6px);

        /* Smooth bottom border */
        border-bottom: 1px solid rgba(255,255,255,0.15);
        margin-bottom: 0;
    }

    .fixed-header-marker { height: 0px; }

</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------
# SIDEBAR (collapsible)
# ----------------------------------------------------
with st.sidebar:
    st.header("Sidebar Settings")
    st.write("This sidebar can collapse and the sticky header still works.")
    show_raw = st.checkbox("Show raw dataset", False)


# ----------------------------------------------------
# Sample data for filtering
# ----------------------------------------------------
data = pd.DataFrame({
    "Category": ["A", "A", "B", "B", "C", "C"] * 10,
    "Item": [f"Item {i}" for i in range(60)],
    "Value": [i * 3 for i in range(60)]
})


# ----------------------------------------------------
# Sticky header (filters)
# ----------------------------------------------------
sticky = st.container()
sticky.markdown("<div class='fixed-header-marker'></div>", unsafe_allow_html=True)

col1, col2, col3 = sticky.columns([1, 2, 1])

with col1:
    category_filter = st.selectbox("Category", ["All", "A", "B", "C"], key="cat")

with col2:
    search_filter = st.text_input("Search item…", key="search")

with col3:
    apply = st.button("Apply Filters", key="apply")


# ----------------------------------------------------
# Apply filtering logic
# ----------------------------------------------------
filtered = data.copy()

if category_filter != "All":
    filtered = filtered[filtered["Category"] == category_filter]

if search_filter:
    filtered = filtered[filtered["Item"].str.contains(search_filter, case=False)]


# ----------------------------------------------------
#Display results
# ----------------------------------------------------
st.write("### Filtered Results")
st.dataframe(filtered)

if show_raw:
    st.write("### Raw Dataset")
    st.dataframe(data)