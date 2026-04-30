import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Sticky Filters + Sidebar",
    layout="wide"
)

# ----------------------------------------------------
# JS: Detect Streamlit theme & expose it as body classes
# ----------------------------------------------------
st.markdown("""
<script>
(function () {
  function detectStreamlitTheme() {
    const bg = getComputedStyle(document.body)
      .getPropertyValue('--background-color')
      .trim();

    if (!bg) return;

    // Extract RGB values
    const rgb = bg.match(/\\d+/g)?.map(Number);
    if (!rgb || rgb.length < 3) return;

    // Perceived luminance
    const luminance =
      0.2126 * rgb[0] +
      0.7152 * rgb[1] +
      0.0722 * rgb[2];

    const isDark = luminance < 128;

    document.body.classList.toggle("st-theme-dark", isDark);
    document.body.classList.toggle("st-theme-light", !isDark);
  }

  // Initial run
  detectStreamlitTheme();

  // Re-run whenever Streamlit mutates the DOM (theme toggle)
  const observer = new MutationObserver(detectStreamlitTheme);
  observer.observe(document.body, {
    attributes: true,
    childList: true,
    subtree: true
  });
})();
</script>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# CSS: Sticky header (explicit colours, theme-aware)
# ----------------------------------------------------
st.markdown("""
<style>
    /* Sticky main filter bar */
    div[data-testid="stVerticalBlock"] div:has(div.sticky-header-marker) {
        position: sticky;
        top: 0;
        z-index: 9999;
        padding-top: 8px;
        padding-bottom: 12px;
        margin-bottom: 0;
        margin-top: -8px;

        /* safe fallback */
        background: var(--secondary-background-color);

        border-bottom: 1px solid var(--sidebar-border-color);
    }

    /* ✅ Light theme (Streamlit app theme, not OS) */
    body.st-theme-light
    div[data-testid="stVerticalBlock"] div:has(div.sticky-header-marker) {
        background: white;
    }

    /* ✅ Dark theme (Streamlit app theme, not OS) */
    body.st-theme-dark
    div[data-testid="stVerticalBlock"] div:has(div.sticky-header-marker) {
        background: #0e1117;
    }

    .sticky-header-marker {
        height: 0px;
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