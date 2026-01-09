import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime
from charts import temperature_line_chart

st.set_page_config(page_title="Weather App", 
                   layout="centered")

initial_states = {
    "current_city": "",
    "weather_data": "",
    "temp_diff": 0,
    "temp_diff_f": 0,
    "temp_unit": "",
    "temp_metric": 0,
    "current_week_day": "",
}

for key, value in initial_states.items():
    if key not in st.session_state:
        st.session_state[key] = value

def get_week_day(time):
    dt = datetime.strptime(time, "%Y-%m-%dT%H:%M")
    return dt.strftime("%A").lower()

def decode_wind_direction(angle):
    directions = [
        ("N", "North"),
        ("NE", "Northeast"),
        ("E", "East"),
        ("SE", "Southeast"),
        ("S", "South"),
        ("SW", "Southwest"),
        ("W", "West"),
        ("NW", "Northwest")
    ]
    index = int((angle + 22.5) % 360 // 45)
    return [directions[index][0], directions[index][1]]

def decode_weathercode(code, is_day=1):
    weather_map = {
        # Sky and Clouds
        0:  ["☀️", "🌙", "Clear sky"],
        1:  ["🌤️", "🌙", "Mainly clear"],
        2:  ["⛅", "☁️", "Partly cloudy"],
        3:  ["☁️", "☁️", "Overcast"],
        # Fog
        45: ["🌫️", "🌫️", "Fog"],
        48: ["🌫️", "🌫️", "Depositing rime fog"],
        # Drizzle
        51: ["🌦️", "🌧️", "Light drizzle"],
        53: ["🌦️", "🌧️", "Moderate drizzle"],
        55: ["🌦️", "🌧️", "Dense drizzle"],
        56: ["❄️", "❄️", "Light freezing drizzle"],
        57: ["❄️", "❄️", "Dense freezing drizzle"],
        # Rain
        61: ["💧", "💧", "Slight rain"],
        63: ["🌧️", "🌧️", "Moderate rain"],
        65: ["🌧️", "🌧️", "Heavy rain"],
        66: ["❄️", "❄️", "Light freezing rain"],
        67: ["❄️", "❄️", "Heavy freezing rain"],
        # Snow
        71: ["🌨️", "🌨️", "Slight snow fall"],
        73: ["🌨️", "🌨️", "Moderate snow fall"],
        75: ["❄️", "❄️", "Heavy snow fall"],
        77: ["🌨️", "🌨️", "Snow grains"],
        # Rain Showers
        80: ["🌦️", "🌧️", "Slight rain showers"],
        81: ["🌧️", "🌧️", "Moderate rain showers"],
        82: ["🌧️", "🌧️", "Violent rain showers"],
        # Snow Showers
        85: ["🌨️", "🌨️", "Slight snow showers"],
        86: ["❄️", "❄️", "Heavy snow showers"],
        # Thunderstorms
        95: ["⛈️", "⛈️", "Thunderstorm"],
        96: ["⛈️", "⛈️", "Thunderstorm with slight hail"],
        99: ["🌩️", "🌩️", "Thunderstorm with heavy hail"]
    }
    
    result = weather_map.get(code, ["🌡️", "🌡️", "Unknown"])
    emoji = result[0] if is_day else result[1]
    description = result[2]
    
    return [emoji, description]

def GET_DATA(id):
    url = "https://api.open-meteo.com/v1/forecast"
    weather_variables = ["temperature_2m", "weather_code", "wind_speed_10m", "wind_direction_10m", "is_day", "precipitation_probability", "relative_humidity_2m"]
    params = {
        "latitude": id["lat"],
        "longitude": id["lon"],
        "hourly":  weather_variables,
        "current": weather_variables,
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "timezone":"auto",
    }

    st.session_state.current_city = f"{id['name']}, {id['address.country']}"
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    st.write(data)

    #temp diffs
    current_dt = datetime.fromisoformat(data["current"]["time"])
    idx = max(
        i for i, t in enumerate(data["hourly"]["time"])
        if datetime.fromisoformat(t) < current_dt
    )
    temp_diff = data["current"]["temperature_2m"] - data["hourly"]["temperature_2m"][idx]
    temp_diff = round(temp_diff, 1)
    st.session_state.temp_diff = temp_diff
    st.session_state.temp_diff_f = int(round(temp_diff * 9 / 5))
    #current data
    current_data = {
        "time": data["current"]["time"],
        "temperature": data["current"]["temperature_2m"],
        "weather_code": data["current"]["weather_code"],
        "wind_speed": data["current"]["wind_speed_10m"],
        "wind_direction": data["current"]["wind_direction_10m"],
        "is_day": data["current"]["is_day"],
        "precipitation_probability": data["current"]["precipitation_probability"],
        "humidity": data["current"]["relative_humidity_2m"]
    }
    #hourl data
    hourly_data = {
        "time": data["hourly"]["time"],
        "temperature": data["hourly"]["temperature_2m"],
        "weather_code": data["hourly"]["weather_code"],
        "wind_speed": data["hourly"]["wind_speed_10m"],
        "wind_direction": data["hourly"]["wind_direction_10m"],
        "is_day": data["hourly"]["is_day"],
        "precipitation_probability": data["hourly"]["precipitation_probability"],
        "humidity": data["hourly"]["relative_humidity_2m"]
    }
    #replace current time value in hourly data
    current_dt = datetime.fromisoformat(current_data["time"])
    idx = max(
        i for i, t in enumerate(hourly_data["time"])
        if datetime.fromisoformat(t) <= current_dt
    )
    #replacing all current values in hourly data
    for key in current_data:
        if key in hourly_data:
            hourly_data[key][idx] = current_data[key]
    #deleting all 
    for key in hourly_data:
        hourly_data[key] = hourly_data[key][idx:]
    #decoding each weathercode
    hourly_data["weather_emoji"] = [decode_weathercode(c, d)[0] for c, d in zip(hourly_data["weather_code"], hourly_data["is_day"])]
    hourly_data["weather_text"]  = [decode_weathercode(c, d)[1] for c, d in zip(hourly_data["weather_code"], hourly_data["is_day"])]
    del hourly_data["weather_code"]
    del hourly_data["is_day"]
    #decoding each wind direction
    hourly_data["wind_acronym"] = [decode_wind_direction(a)[0] for a in hourly_data["wind_direction"]]
    hourly_data["wind_point"]   = [decode_wind_direction(a)[1] for a in hourly_data["wind_direction"]]
    del hourly_data["wind_direction"]
    #separating df by week
    week_data = {}
    for i, t in enumerate(hourly_data["time"]):
        day = datetime.strptime(t, "%Y-%m-%dT%H:%M").strftime("%A").lower()
        row = {k: hourly_data[k][i] for k in hourly_data}
        week_data.setdefault(day, []).append(row)
    for d in week_data:
        week_data[d] = pd.DataFrame(week_data[d])
    #down to max 8 rows in each DF
    for d in week_data:
        df = week_data[d]
        if len(df) > 8:
            idx = np.linspace(0, len(df) - 1, 8, dtype=int)
            week_data[d] = df.iloc[idx].reset_index(drop=True)
    #adding fahrenheit column
    for d in week_data:
        df = week_data[d]
        df["temperature"] = df["temperature"].round().astype(int)
        df["wind_speed"]  = df["wind_speed"].round().astype(int)
        df["temperature_f"] = (df["temperature"] * 9 / 5 + 32).round().astype(int)

    st.session_state.weather_data = week_data
    st.write(st.session_state.weather_data)
    st.dataframe(st.session_state.weather_data['saturday'])

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
        st.markdown(body=f"Rain: <br>Humidity: <br>Wind: ",
                        text_alignment="justify",
                        unsafe_allow_html=True,
                        )
if False:
    main()

#problema quando o grafico so tem um dado
