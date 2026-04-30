import streamlit as st
import streamlit.components.v1 as components

st.title("JS → Streamlit sanity check")

value = components.html(
    """
    <script>
    window.parent.postMessage(
        {
            isStreamlitMessage: true,
            type: "streamlit:setComponentValue",
            value: "#123456"
        },
        "*"
    );
    </script>
    """,
    height=0,
)

st.write("Returned value:")
st.write(value)