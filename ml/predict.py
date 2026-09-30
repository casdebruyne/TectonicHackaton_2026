import joblib
import pandas as pd

model = joblib.load("ml/models/model.pkl")

def predict(input_data):
    df = pd.DataFrame([input_data])
    return model.predict(df)[0]

