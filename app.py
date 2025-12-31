import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Weather App", 
                   layout="centered")
initial_states = {
    "current_temp": 0,
    "past_temp": 0,
    "temp_diff": 0,
    "temp_unit": "",
}
for key, value in initial_states.items():
    if key not in st.session_state:
        st.session_state[key] = value

def show_temperature(id):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": id["lat"],
        "longitude": id["lon"],
        "hourly": "temperature_2m",
        "current": "temperature_2m",
        "temperature_unit": "celsius",
        "timezone":"auto",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    st.write(data)

    current_temperature = data["current"]["temperature_2m"]
    current_time = data["current"]["time"]

    data_time = data["hourly"]["time"]
    data_temperature= data["hourly"]["temperature_2m"]

    past_temp= data_temperature[data_time.index(current_time[:-2] + "00") - 1]

    temp_unit = data["current_units"]["temperature_2m"]

    st.session_state.current_temp = current_temperature
    st.session_state.past_temp = past_temp
    st.session_state.temp_diff = st.session_state.current_temp - st.session_state.past_temp
    st.session_state.temp_unit = temp_unit

def search_city(city):
    with st.spinner("Wait for it..."):
        headers={"User-Agent": "weather-app (github.com/murilobispo)"}
        url = f"https://nominatim.openstreetmap.org/search?format=json&addressdetails=1&accept-language=en&q={city}"
        try:
            response = requests.get(url,headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            if not data:
                st.warning("City not found")
            else:
                df = pd.json_normalize(data)
                df = df[df["addresstype"].isin(["city", "municipality", "town"])].reset_index(drop=True)
                if df.empty:
                    st.warning("Enter only cities")
                elif len(df) == 1:
                    show_temperature(df.iloc[0].to_dict())
                else:
                    placeholder = st.empty()
                    addresses = (df["name"] + ", " + df["address.state"] + ", " + df["address.country"]).tolist()
                    options =  dict(zip(df["place_id"], addresses))
                    with placeholder:
                        selected = st.pills(label="Do you mean:", 
                                            options=options.keys(),
                                            format_func=lambda option: options[option],
                                            selection_mode="single",
                                            key="city_pills"
                                            )
                    if selected:
                        placeholder.empty() 
                        show_temperature(df.loc[df["place_id"] == selected].iloc[0].to_dict())

        except requests.exceptions.RequestException as e:
            st.error(f"Error {e}")

city_input = st.text_input(label="city-input",
                           key="city-input",
                           value=None,
                           label_visibility="hidden",
                           placeholder="city"
                           )
if city_input:
    search_city(city_input)

metric = st.metric(label="Temperature", 
                   value=f"{round(st.session_state.current_temp)} {st.session_state.temp_unit}", 
                   delta=round(st.session_state.temp_diff, 1),
                   )
