import streamlit as st
import pandas as pd
import requests
from services.open_meteo import GET_DATA

def search_city(city):
    with st.spinner('Wait for it...'):
        headers={'User-Agent': 'weather-app (github.com/murilobispo)'}
        url = f'https://nominatim.openstreetmap.org/search?format=json&addressdetails=1&accept-language=en&q={city}'
        try:
            response = requests.get(url,headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            if not data:
                st.warning('City not found')
            else:
                df = pd.json_normalize(data)
                df = df[df['addresstype'].isin(['city', 'municipality', 'town'])].reset_index(drop=True)
                if df.empty:
                    st.warning('Enter only cities')
                elif len(df) == 1:
                    GET_DATA(df.iloc[0].to_dict())
                else:
                    placeholder = st.empty()
                    addresses = (df['name'] + ', ' + df['address.state'] + ', ' + df['address.country']).tolist()
                    options =  dict(zip(df["place_id"], addresses))
                    with placeholder:
                        selected = st.pills(label='Do you mean:', 
                                            options=options.keys(),
                                            format_func=lambda option: options[option],
                                            selection_mode='single',
                                            key='city_pills'
                                            )
                    if selected:
                        placeholder.empty() 
                        GET_DATA(df.loc[df['place_id'] == selected].iloc[0].to_dict())

        except requests.exceptions.RequestException as e:
            st.error(f"Error {e}")