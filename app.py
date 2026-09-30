import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="HACKATON App",
    page_icon="🎈",
    layout="wide",
)

st.title("HACKATON")

with st.sidebar:
    st.header("About app")
    st.write("This is my first app.")
    st.write("gailly geitje")
    st.write("##niggers niggers hate niggers")

st.header("Interactive demo")
st.markdown("This is created using `st.markdown`.")

@st.cache_data
def get_chart_data():
    return pd.DataFrame(np.random.randn(10, 3), columns=["A", "B", "C"])

col1, col2 = st.columns(2)

with col1:
    x_value = st.slider("Choose an x value", min_value=1, max_value=10, value=5)

with col2:
    st.metric("Current x value", x_value)

st.subheader("Area chart")
chart_data = get_chart_data()
st.area_chart(chart_data)

if st.button("🎈 Show surprise"):
    st.balloons()
    st.success("Surprise activated!")

# Optional: clean embedded HTML
components.html(
    """
    <div id="b" style="font-size:80px; cursor:pointer; text-align:center; user-select:none;">🎈</div>
    <div id="player"></div>
    <script>
    const b = document.getElementById("b");
    const player = document.getElementById("player");

    b.onclick = () => {
      b.textContent = "💥";
      setTimeout(() => { b.textContent = "🎈"; }, 800);
      player.innerHTML = '<iframe width="100%" height="300" ' +
        'src="https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1" ' +
        'allow="autoplay; encrypted-media" frameborder="0"></iframe>';
    };
    </script>
    """,
    height=320,
)
