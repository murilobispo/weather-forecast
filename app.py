import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Weather App", layout="centered")

def get_data(city):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=10&language=en&format=json"
    response = requests.get(url).json()["results"]
    df = pd.DataFrame(response)
    df = df[["name", "country","country_code", "admin1", "latitude", "longitude","timezone","feature_code"]]

    st.dataframe(df, use_container_width=True)


city_input = st.text_input(label="city-input",
                           key="city-input",
                           value=None,
                           label_visibility="hidden",
                           placeholder="city"
                           )
if city_input:
    get_data(city_input)

#metric = st.metric(label="Tempeture", 
                #value="70 °F", )
