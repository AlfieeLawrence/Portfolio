st.markdown("""
<style>

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

    /* ✅ Theme-aware, guaranteed to update */
    background-color: var(--background-color);
    color: var(--text-color);

    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--secondary-background-color);
}

/* Marker */
.sticky-banner-marker {
    height: 0;
}

</style>
""", unsafe_allow_html=True)