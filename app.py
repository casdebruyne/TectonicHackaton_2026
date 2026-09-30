import streamlit as st
import pandas as pd
import numpy as np
import time

st.title("HACKATON")

with st.sidebar:
    st.header("About app")
    st.write("This is my first app.")
     st.divider()
    st.subheader("⚙️ Instellingen")
    n_points = st.slider("Aantal datapunten", 10, 200, 50)
    chart_type = st.selectbox("Type grafiek", ["Area", "Line", "Bar"])
    show_data = st.checkbox("Toon ruwe data", value=False)
    theme_color = st.color_picker("Kies een kleur", "#FF4B4B")
    st.divider()
    if st.button("🎈 Verras me!"):
        st.balloons()

st.header("This is a header with a divider", divider="rainbow")
st.markdown("This is created using **st.markdown** — nu met *extra's*! ✨")

col1, col2 = st.columns(2)

with col1:
    x = st.slider("Choose an x value",1,10)
with col2:
    st.write("The value of x is", x)

chart_data = pd.DataFrame(np.random.randn(10,3), columns=["A","B","C"])
st.area_chart(chart_data)

