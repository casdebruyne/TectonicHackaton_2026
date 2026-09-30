import numpy as np
import pandas as pd
import streamlit as st

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
    return pd.DataFrame(rng.normal(size=(10, 3)), columns=["A", "B", "C"])


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
st.area_chart(get_chart_data())

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
