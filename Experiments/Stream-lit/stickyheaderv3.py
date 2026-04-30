import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

st.title("Detect App Background Color via JavaScript")

# -----------------------------------------------------------------------------
# JavaScript → Streamlit component
# -----------------------------------------------------------------------------
bg_hex = components.html(
    """
    <script>
    function rgbToHex(rgb) {
        const nums = rgb.match(/\\d+/g);
        if (!nums) return null;
        return "#" + nums
            .slice(0, 3)
            .map(v => parseInt(v).toString(16).padStart(2, "0"))
            .join("");
    }

    function reportBackground() {
        // Streamlit-defined CSS variable
        const bg = getComputedStyle(document.body)
            .getPropertyValue("--background-color") ||
            getComputedStyle(document.body).backgroundColor;

        const hex = rgbToHex(bg);

        if (hex) {
            window.parent.postMessage(
                {
                    isStreamlitMessage: true,
                    type: "streamlit:setComponentValue",
                    value: hex
                },
                "*"
            );
        }
    }

    setTimeout(reportBackground, 100);
    </script>
    """,
    height=0,
)

# -----------------------------------------------------------------------------
# Python receives the JS value here
# -----------------------------------------------------------------------------
if bg_hex is not None:
    st.write("Detected background color (hex):")
    st.code(bg_hex)

    st.markdown(
        f"""
        <div style="
            width: 160px;
            height: 80px;
            background-color: {bg_hex};
            border-radius: 6px;
            border: 1px solid rgba(0,0,0,0.25);
        "></div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.info("Waiting for browser to report background color…")