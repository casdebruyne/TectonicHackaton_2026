import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="HACKATON",
    page_icon="🎈",
    layout="wide",
)

# --------------------------------------------------
# Helper functions
# --------------------------------------------------
@st.cache_data
def get_chart_data():
    rng = np.random.default_rng(42)
    return pd.DataFrame(np.random.randn(10, 3), columns=["A", "B", "C"])


def render_surprise_image():
    components.html(
        <div id="b" style="font-size:80px; cursor:pointer; text-align:center; user-select:none;">🎈</div>
        <div id="imageContainer"></div>
        <script>
        const b = document.getElementById("b");
        const container = document.getElementById("imageContainer");
    )


# --------------------------------------------------
# App layout
# --------------------------------------------------
st.title("HACKATON")

with st.sidebar:
    st.header("About app")
    st.write("This is my first app.")
    st.write("gailly geitje")
    st.caption("Built with Streamlit")

st.header("Interactive dashboard")
st.markdown("This is created using `st.markdown`.")

# -------------------------
# Slider and metric
# -------------------------
col1, col2 = st.columns(2)

with col1:
    x_value = st.slider(
        "Choose an x value",
        min_value=1,
        max_value=10,
        value=5,
        step=1,
    )

with col2:
    st.metric("Current x value", x_value)

# -------------------------
# Random chart
# -------------------------
st.subheader("Area chart")
chart_data = get_chart_data()
st.area_chart(chart_data)

# -------------------------
# Surprise button
# -------------------------
if "surprise_open" not in st.session_state:
    st.session_state.surprise_open = False

if st.button("🎈 Surprise me!"):
    st.session_state.surprise_open = not st.session_state.surprise_open
    if st.session_state.surprise_open:
        st.balloons()
        st.success("Surprise activated!")

if st.session_state.surprise_open:
    render_surprise_image()
