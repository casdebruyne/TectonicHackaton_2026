import streamlit is st
import pandas as pd
data = pd.read_csv("business-financial-data-June-2026-quarter.csv")
st.write(data)
