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
