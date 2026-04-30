import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Sticky Filters + Sidebar",
    layout="wide"
)

# ----------------------------------------------------
# Sticky header styling (theme-aware, boxed, no bleed)
# ----------------------------------------------------
st.markdown("""
<style>
    /* Sticky positioning layer */
    div[data-testid="stVerticalBlock"] 
    > div:has(div.sticky-header-marker) {

        position: sticky;
        top: 0;
        z-index: 9999;

        margin-top: -8px;
        margin-bottom: 0;
    }

    /* Visible header "box" */
    div[data-testid="stVerticalBlock"] 
    > div:has(div.sticky-header-marker)
    > div {

        background-color: var(--background-color);
        padding: 8px 16px 12px 16px;

        border-bottom: 1px solid var(--sidebar-border-color);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
    }

    /* Marker element */
    .sticky-header-marker {
        height: 0;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# SIDEBAR
# ----------------------------------------------------
with st.sidebar:
    st.header("Sidebar Settings")
    st.write("This sidebar can collapse and the sticky header still works.")
    show_raw = st.checkbox("Show raw dataset", False)

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
    "<div class='sticky-header-marker'></div>",
    unsafe_allow_html=True
)

col1, col2, col3 = sticky.columns([1, 2, 1])

with col1:
    category_filter = st.selectbox(
        "Category",
        ["All", "A", "B", "C"]
    )

with col2:
    search_filter = st.text_input(
        "Search item…"
    )

with col3:
    apply = st.button(
        "Apply Filters"
    )

# ----------------------------------------------------
# Filter logic
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

# Extra rows to prove stickiness
for _ in range(3):
    st.write("### Filtered Results")
    st.dataframe(filtered)