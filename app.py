import numpy as np
import pandas as pd
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="HACKATON",
    page_icon="🎈",
    layout="wide",
)

data = pd.read_csv("business-financial-data-June-2026-quarter.csv") #### vervang hier de naam door het csv bestand dat we gegeven krijgen###
st.write(data)

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
st.title("Hello World!")

with st.sidebar:
    st.header("About app")
    st.write("suck my fat one")
    st.write("This is my first app.")

st.header("This is a header with a divider")

st.header("Interactive dashboard")
st.markdown("This is created using `st.markdown`.")
st.markdown("This is created using st.markdown")

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

    x = st.slider("Choose an x value",1,10)
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
    st.write("The value of x is", x)

if st.button("🎈 Surprise me!"):
    st.session_state.surprise_open = not st.session_state.surprise_open
    if st.session_state.surprise_open:
        st.balloons()
        st.success("Surprise activated!")
chart_data = pd.DataFrame(np.random.randn(10,3), columns=["A","B","C"])
st.area_chart(chart_data)
