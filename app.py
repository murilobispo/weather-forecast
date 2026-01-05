import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime
from charts import temperature_line_chart

st.set_page_config(page_title="Weather App", 
                   layout="centered")

initial_states = {
    "current_temp": 0,
    "current_time": "",
    "current_city": "",
    "current_week_day": "",
    "weather_description": ["",""],
    "week_temperature_data": "",
    "past_temp": 0,
    "temp_diff": 0,
    "temp_unit": "",
}
for key, value in initial_states.items():
    if key not in st.session_state:
        st.session_state[key] = value

def get_week_day(time):
    dt = datetime.strptime(time, "%Y-%m-%dT%H:%M")
    return dt.strftime("%A").lower()

def decode_weathercode(code):
    weather_map = {
        # Sky and Clouds
        0:  ["☀️", "Clear sky"],
        1:  ["🌤️", "Mainly clear"],
        2:  ["⛅", "Partly cloudy"],
        3:  ["☁️", "Overcast"],
        # Fog
        45: ["🌫️", "Fog"],
        48: ["🌫️", "Depositing rime fog"],
        # Drizzle
        51: ["🌦️", "Light drizzle"],
        53: ["🌦️", "Moderate drizzle"],
        55: ["🌦️", "Dense drizzle"],
        56: ["❄️", "Light freezing drizzle"],
        57: ["❄️", "Dense freezing drizzle"],
        # Rain
        61: ["💧", "Slight rain"],
        63: ["🌧️", "Moderate rain"],
        65: ["🌧️", "Heavy rain"],
        66: ["❄️", "Light freezing rain"],
        67: ["❄️", "Heavy freezing rain"],
        # Snow
        71: ["🌨️", "Slight snow fall"],
        73: ["🌨️", "Moderate snow fall"],
        75: ["❄️", "Heavy snow fall"],
        77: ["🌨️", "Snow grains"],
        # Rain Showers
        80: ["🌦️", "Slight rain showers"],
        81: ["🌧️", "Moderate rain showers"],
        82: ["🌧️", "Violent rain showers"],
        # Snow Showers
        85: ["🌨️", "Slight snow showers"],
        86: ["❄️", "Heavy snow showers"],
        # Thunderstorms
        95: ["⛈️", "Thunderstorm"],
        96: ["⛈️", "Thunderstorm with slight hail"],
        99: ["🌩️", "Thunderstorm with heavy hail"]
    }
    
    return weather_map.get(code, ["🌡️", "Unknown"])

def GET_DATA(id):
    url = "https://api.open-meteo.com/v1/forecast"
    weather_variables = ["temperature_2m", "weather_code", "wind_speed_10m", "wind_direction_10m", "rain", "is_day", "precipitation_probability"]
    params = {
        "latitude": id["lat"],
        "longitude": id["lon"],
        "hourly":  weather_variables,
        "current": weather_variables,
        "temperature_unit": "celsius",
        "timezone":"auto",
    }

    st.session_state.current_city = f"{id['name']}, {id['address.country']}"
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    st.write(data)
    
    current_temperature = data["current"]["temperature_2m"]
    current_time = data["current"]["time"]

    current_code = data["current"]["weather_code"]

    hourly_temperature = data["hourly"]["temperature_2m"]
    hourly_temperature = [round(i) for i in hourly_temperature]
    hourly_time = data["hourly"]["time"]
    hourly_code = data["hourly"]["weather_code"]
    hourly_description_text = [decode_weathercode(c)[1] for c in hourly_code]
    hourly_description_emoji = [decode_weathercode(c)[0] for c in hourly_code]
    
    if (current_time[:-2] + "00") == current_time:
        st.session_state.past_temp = hourly_temperature[hourly_time.index(current_time) - 1]
    else:
        st.session_state.past_temp = hourly_temperature[hourly_time.index(current_time[:-2] + "00")]
    
    temp_unit = data["current_units"]["temperature_2m"]

    week_temperature = pd.DataFrame({
        "time": hourly_time,
        "temperature_2m": hourly_temperature,
        "description_text": hourly_description_text,
        "description_emoji": hourly_description_emoji
    })
    week_temperature["weekday"] = week_temperature["time"].apply(get_week_day)
    week_temperature["time"] = pd.to_datetime(week_temperature["time"])

    week_dict = {}
    for day in week_temperature["weekday"].unique():  
        week_dict[day] = week_temperature[week_temperature["weekday"] == day]\
                            .drop(columns="weekday")\
                            .reset_index(drop=True)

    for i, day in enumerate(list(week_dict.keys())):
        if i == 0:
            week_dict[day] = week_dict[day][
                week_dict[day]["time"] >= (current_time[:-2] + "00")
            ].reset_index(drop=True)

            week_dict[day].loc[0, "time"] = current_time
            week_dict[day].loc[0, "temperature_2m"] = current_temperature
            if len(week_dict[day]) > 8:
                week_dict[day] = week_dict[day].iloc[
                    np.linspace(0, len(week_dict[day]) - 1, 8).astype(int)
                ].reset_index(drop=True)
        else:
            week_dict[day] = week_dict[day].iloc[::3].reset_index(drop=True)
    for day in week_dict:
        week_dict[day]["time"] = pd.to_datetime(
            week_dict[day]["time"]
        ).dt.strftime("%H:%M")

    #st.write(week_dict)
    st.session_state.current_temp = current_temperature
    st.session_state.current_time = current_time
    st.session_state.current_week_day = get_week_day(current_time)
    st.session_state.weather_description = decode_weathercode(current_code)
    st.session_state.temp_diff = st.session_state.current_temp - st.session_state.past_temp
    st.session_state.temp_unit = temp_unit
    st.session_state.week_temperature_data = week_dict

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
                    GET_DATA(df.iloc[0].to_dict())
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
                        GET_DATA(df.loc[df["place_id"] == selected].iloc[0].to_dict())

        except requests.exceptions.RequestException as e:
            st.error(f"Error {e}")

city_input = st.text_input(label="city-input",
                           key="city-input",
                           value=None,
                           label_visibility="hidden",
                           placeholder="city",
                           )
if city_input:
    search_city(city_input)

@st.fragment
def main():
    if "current_week_day" not in st.session_state or st.session_state.current_week_day not in st.session_state.week_temperature_data:
        st.session_state.current_week_day = list(st.session_state.week_temperature_data.keys())[0]
    st.segmented_control(
        label="Week Selection",
        label_visibility="collapsed",
        options=list(st.session_state.week_temperature_data.keys()),
        format_func=lambda x: x[:3],
        key="current_week_day"
    )

    col0, col1 = st.columns([2,1],
                            vertical_alignment="center",
                            gap="medium",
                            )
    with col0:
        subCol0, subCol1 = st.columns(2,
                                    vertical_alignment="center",
                                    )
        with subCol0:
            metric = st.metric(label=st.session_state.current_city, 
                            value=f"{st.session_state.weather_description[0]}{round(st.session_state.current_temp)} {st.session_state.temp_unit}", 
                            delta= None if st.session_state.temp_diff == 0 else f"{round(st.session_state.temp_diff, 1)} {st.session_state.temp_unit}",
                            width="stretch",
                            )
        with subCol1:
            st.markdown(body=f"**Weather**<br>{st.session_state.current_week_day}, {st.session_state.current_time[-5:]}<br>{st.session_state.weather_description[1]}",
                        text_alignment="right",
                        unsafe_allow_html=True,
                        width="stretch"
                        )
    with col1:
        st.image("https://png.pngtree.com/thumb_back/fh260/background/20240408/pngtree-clouds-in-sky-sky-in-summer-weather-upstairs-summer-day-image_15651093.jpg", 
                width="stretch",
                )

    col3, col4 = st.columns([2, 1], vertical_alignment="center")
    with col3:
        tab1, tab2, tab3 = st.tabs(["Temperature", "Rain", "Wind"])
        with tab1:
            fig = temperature_line_chart(st.session_state.week_temperature_data[st.session_state.current_week_day], "time", 'temperature_2m')
            chart = st.plotly_chart(fig, theme="streamlit", on_select="rerun", config={"displayModeBar": False})
            if chart:
                st.write(chart)

    with col4:
        st.markdown(body=f"Rain<br>Humidity<br>Wind",
                        text_alignment="center",
                        unsafe_allow_html=True,
                        )
if st.session_state.current_city:
    main()
