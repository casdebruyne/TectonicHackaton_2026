import streamlit as st
import pandas as pd
import numpy as np

st.title("HACKATON")

with st.sidebar:
    st.header("About app")
    st.write("This is my first app.")
st.header("This is a header with a divider")
st.markdown("This is created using st.markdown")
col1, col2 = st.columns(2)

with col1:
    x = st.slider("Choose an x value",1,10)
with col2:
    st.write("The value of x is", x)

chart_data = pd.DataFrame(np.random.randn(10,3), columns=["A","B","C"])
st.area_chart(chart_data)

if st.button("🎈 Verras me!"):
    st.balloons()
import streamlit.components.v1 as components

components.html("""
<div id="b" style="font-size:80px; cursor:pointer; text-align:center; user-select:none;">🎈</div>
<div id="player"></div>
<script>
const b = document.getElementById("b");
const player = document.getElementById("player");
b.onclick = () => {
  b.textContent = "💥";
  setTimeout(() => { b.textContent = "🎈"; }, 800);
  player.innerHTML = '<iframe width="300" height="170" ' +
    'src="https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1" ' +
    'allow="autoplay; encrypted-media" frameborder="0"></iframe>';
};
</script>
""", height=320)
