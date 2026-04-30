import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Sticky Filters + Sidebar",
    layout="wide"
)

# ----------------------------------------------------
# Read theme colours from Streamlit config (SUPPORTED)
# ----------------------------------------------------
theme_base = st.get_option("theme.base")
bg = st.get_option("theme.backgroundColor")
secondary_bg = st.get_option("theme.secondaryBackgroundColor")
text_color = st.get_option("theme.textColor")

# ----------------------------------------------------
# Sticky header styling (CONFIG‑DRIVEN)
# ----------------------------------------------------
st.markdown(f"""
<style>

/* Sticky main filter bar */
div[data-testid="stVerticalBlock"]
div:has(div.fixed-header-marker) {{
    position: sticky;
    top: 0;
    z-index: 9999;

    padding-top: 8px;
    padding-bottom: 8px;

    /* ✅ CONFIGURED SECONDARY BACKGROUND */
    background-color: {secondary_bg};
    color: {text_color};

    /* Optional visual polish */
    backdrop-filter: blur(6px);
    border-bottom: 1px solid rgba(255,255,255,0.15);
    margin-bottom: 0;

    /* Prevent transparency bleed */
    isolation: isolate;
}}

.fixed-header-marker {{
    height: 0px;
}}

</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# SIDEBAR (collapsible)
# ----------------------------------------------------
with st.sidebar:
    st.header("Sidebar Settings")
    st.write("This sidebar can collapse and the sticky header still works.")
    show_raw = st.checkbox("Show raw dataset", False)

    st.divider()
    st.caption("Theme info (from config)")
    st.code(f"""
Base: {theme_base}
Background: {bg}
Secondary: {secondary_bg}
""")

# ----------------------------------------------------
# Sample data
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
sticky.markdown(
    "<div class='fixed-header-marker'></div>",
    unsafe_allow_html=True
)

col1, col2, col3 = sticky.columns([1, 2, 1])

with col1:
    category_filter = st.selectbox(
        "Category",
        ["All", "A", "B", "C"],
        key="cat"
    )

with col2:
    search_filter = st.text_input(
        "Search item…",
        key="search"
    )

with col3:
    apply = st.button(
        "Apply Filters",
        key="apply"
    )

# ----------------------------------------------------
# Apply filtering
# ----------------------------------------------------
filtered = data.copy()

if category_filter != "All":
    filtered = filtered[filtered["Category"] == category_filter]

if search_filter:
    filtered = filtered[
        filtered["Item"].str.contains(search_filter, case=False)
    ]

# ----------------------------------------------------
# Display results
# ----------------------------------------------------
st.write("### Filtered Results")
st.dataframe(filtered)

if show_raw:
    st.write("### Raw Dataset")
    st.dataframe(data)