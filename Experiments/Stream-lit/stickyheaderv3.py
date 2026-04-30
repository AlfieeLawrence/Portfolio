import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

st.title("Detect App Background Color via JavaScript")

# -----------------------------------------------------------------------------
# JavaScript → Streamlit bridge component
# -----------------------------------------------------------------------------
color_hex = components.html(
    """
    <div id="root"></div>

    <script>
    function rgbToHex(rgb) {
        const result = rgb.match(/\\d+/g);
        if (!result) return null;
        return "#" + result
            .slice(0, 3)
            .map(x => parseInt(x).toString(16).padStart(2, "0"))
            .join("");
    }

    function getBackgroundHex() {
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

    // Run once after render
    setTimeout(getBackgroundHex, 100);
    </script>
    """,
    height=0,
)

# -----------------------------------------------------------------------------
# Python receives value from JS
# -----------------------------------------------------------------------------
if color_hex:
    st.write("Detected background colour (hex):")
    st.code(color_hex)

    st.markdown(
        f"""
        <div style="
            width: 150px;
            height: 80px;
            background-color: {color_hex};
            border: 1px solid rgba(0,0,0,0.2);
            border-radius: 6px;
        "></div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.info("Waiting for JavaScript to report background colour…")
