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
    return pd.DataFrame(rng.standard_normal(10, 3), columns=["A", "B", "C"])


def render_surprise_image():
    components.html(
        """
        <div id="b" style="font-size:80px; cursor:pointer; text-align:center; user-select:none;">🎈</div>
        <div id="imageContainer"></div>
        <script>
        const b = document.getElementById("b");
        const container = document.getElementById("imageContainer");

        b.onclick = () => {
          b.textContent = "💥";
          setTimeout(() => { b.textContent = "🎈"; }, 800);
          
          // Fullscreen image display
          const img = document.createElement("img");
          img.src = "funny.jpg";
          img.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: contain;
            background-color: black;
            z-index: 9999;
            cursor: pointer;
          `;
          
          img.onclick = () => img.remove(); // Klik op de afbeelding om te sluiten
          document.body.appendChild(img);
        };
        </script>
        """,
        height=320,
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
