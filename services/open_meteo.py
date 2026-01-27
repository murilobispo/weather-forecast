import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

def get_week_day(time):
    dt = datetime.strptime(time, '%Y-%m-%dT%H:%M')
    return dt.strftime('%A').lower()

def decode_wind_direction(angle):
    angle = (angle + 180) % 360
    directions = [
        ('N', 'North'),
        ('NNE', 'North-Northeast'),
        ('NE', 'Northeast'),
        ('ENE', 'East-Northeast'),
        ('E', 'East'),
        ('ESE', 'East-Southeast'),
        ('SE', 'Southeast'),
        ('SSE', 'South-Southeast'),
        ('S', 'South'),
        ('SSW', 'South-Southwest'),
        ('SW', 'Southwest'),
        ('WSW', 'West-Southwest'),
        ('W', 'West'),
        ('WNW', 'West-Northwest'),
        ('NW', 'Northwest'),
        ('NNW', 'North-Northwest'),
    ]

    index = int((angle + 11.25) % 360 // 22.5)
    return [directions[index][0], directions[index][1]]

def decode_weathercode(code, is_day=1):
    weather_map = {
        # Sky and Clouds
        0:  ['☀️', '🌙', 'Clear sky'],
        1:  ['🌤️', '🌙', 'Mainly clear'],
        2:  ['⛅', '☁️', 'Partly cloudy'],
        3:  ['☁️', '☁️', 'Overcast'],
        # Fog
        45: ['🌫️', '🌫️', 'Fog'],
        48: ['🌫️', '🌫️', 'Depositing rime fog'],
        # Drizzle
        51: ['🌦️', '🌧️', 'Light drizzle'],
        53: ['🌦️', '🌧️', 'Moderate drizzle'],
        55: ['🌦️', '🌧️', 'Dense drizzle'],
        56: ['❄️', '❄️', 'Light freezing drizzle'],
        57: ['❄️', '❄️', 'Dense freezing drizzle'],
        # Rain
        61: ['💧', '💧', 'Slight rain'],
        63: ['🌧️', '🌧️', 'Moderate rain'],
        65: ['🌧️', '🌧️', 'Heavy rain'],
        66: ['❄️', '❄️', 'Light freezing rain'],
        67: ['❄️', '❄️', 'Heavy freezing rain'],
        # Snow
        71: ['🌨️', '🌨️', 'Slight snow fall'],
        73: ['🌨️', '🌨️', 'Moderate snow fall'],
        75: ['❄️', '❄️', 'Heavy snow fall'],
        77: ['🌨️', '🌨️', 'Snow grains'],
        # Rain Showers
        80: ['🌦️', '🌧️', 'Slight rain showers'],
        81: ['🌧️', '🌧️', 'Moderate rain showers'],
        82: ['🌧️', '🌧️', 'Violent rain showers'],
        # Snow Showers
        85: ['🌨️', '🌨️', 'Slight snow showers'],
        86: ['❄️', '❄️', 'Heavy snow showers'],
        95: ['⛈️', '⛈️', 'Thunderstorm'],
        96: ['⛈️', '⛈️', 'Thunderstorm with slight hail'],
        99: ['🌩️', '🌩️', 'Thunderstorm with heavy hail']
        # Thunderstorms
    }
    
    result = weather_map.get(code, ['🌡️', '🌡️', 'Unknown'])
    emoji = result[0] if is_day else result[1]
    description = result[2]
    
    return [emoji, description]

def GET_DATA(id):
    url = 'https://api.open-meteo.com/v1/forecast'
    weather_variables = ['temperature_2m', 'weather_code', 'wind_speed_10m', 'wind_direction_10m', 'is_day', 'precipitation_probability']
    params = {
        'latitude': id['lat'],
        'longitude': id['lon'],
        'hourly':  weather_variables,
        'current': weather_variables,
        'temperature_unit': 'celsius',
        'wind_speed_unit': 'kmh',
        'timezone':'auto'
    }

    st.session_state.current_city = f'{id["name"]}, {id["address.country"]}'
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    #temp diffs
    current_dt = datetime.fromisoformat(data['current']['time'])
    past_indexes = [
        i for i, t in enumerate(data['hourly']['time'])
        if datetime.fromisoformat(t) < current_dt
    ]
    if not past_indexes:
        temp_diff = 0.0
    else:
        idx = max(past_indexes)
        temp_diff = data['current']['temperature_2m'] - data['hourly']['temperature_2m'][idx]
        temp_diff = round(temp_diff, 1)
    st.session_state.temp_diff = temp_diff
    st.session_state.temp_diff_f = round(temp_diff * 9 / 5, 1)
    #current data
    current_data = {
        'time': data['current']['time'],
        'temperature': data['current']['temperature_2m'],
        'weather_code': data['current']['weather_code'],
        'wind_speed': data['current']['wind_speed_10m'],
        'wind_direction': data['current']['wind_direction_10m'],
        'is_day': data['current']['is_day'],
        'precipitation_probability': data['current']['precipitation_probability'],
    }
    #hourl data
    hourly_data = {
        'time': data['hourly']['time'],
        'temperature': data['hourly']['temperature_2m'],
        'weather_code': data['hourly']['weather_code'],
        'wind_speed': data['hourly']['wind_speed_10m'],
        'wind_direction': data['hourly']['wind_direction_10m'],
        'is_day': data['hourly']['is_day'],
        'precipitation_probability': data['hourly']['precipitation_probability'],
    }
    #replace current time value in hourly data
    current_dt = datetime.fromisoformat(current_data['time'])
    idx = max(
        i for i, t in enumerate(hourly_data['time'])
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
    hourly_data['weather_emoji'] = [decode_weathercode(c, d)[0] for c, d in zip(hourly_data['weather_code'], hourly_data['is_day'])]
    hourly_data['weather_text']  = [decode_weathercode(c, d)[1] for c, d in zip(hourly_data['weather_code'], hourly_data['is_day'])]
    del hourly_data["weather_code"]
    del hourly_data["is_day"]
    #decoding each wind direction
    hourly_data['wind_acronym'] = [decode_wind_direction(a)[0] for a in hourly_data['wind_direction']]
    hourly_data['wind_point']   = [decode_wind_direction(a)[1] for a in hourly_data['wind_direction']]
    #del hourly_data["wind_direction"]
    #separating df by week
    week_data = {}
    for i, t in enumerate(hourly_data['time']):
        day = datetime.strptime(t, '%Y-%m-%dT%H:%M').strftime('%A').lower()
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
    #formating time
    for df in week_data.values():
        df['time'] = (
            pd.to_datetime(df['time'])
            .dt.strftime('%H:%M')
        )
    #adding fahrenheit column
    for d in week_data:
        df = week_data[d]
        df['temperature'] = df['temperature'].round().astype(int)
        df['wind_speed']  = df['wind_speed'].round().astype(int)
        df['temperature_f'] = (df['temperature'] * 9 / 5 + 32).round().astype(int)

    st.session_state.weather_data = week_data
    st.session_state.week_day = st.session_state.week_day_cache = (get_week_day(data['current']['time']))
    st.session_state.new_data = True