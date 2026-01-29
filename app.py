import streamlit as st

from utils.charts import temperature_chart
from utils.charts import rain_chart
from utils.charts import wind_chart
from services.nominatim import search_city

st.set_page_config(page_title='Weather App', layout='centered', page_icon='🌦️')

initial_states = {
    'current_city': '',
    'weather_data': '',
    'temp_diff': 0,
    'temp_diff_f': 0,
    'fahrenheit': False,
    'week_day': '',
    'week_day_cache': '',
    'chart_click': {},
    'force_default' : False,
    'new_data': True
}

for key, value in initial_states.items():
    if key not in st.session_state:
        st.session_state[key] = value

st.markdown('''
<style>
.block-container {
    max-width: 700px;
    }
</style>
''', unsafe_allow_html=True)
st.title("Weather Forecast", text_alignment="center")
with st.container(horizontal_alignment='center'):
    city_input = st.text_input(label='city-input',
                            key='city-input',
                            value=None,
                            label_visibility='hidden',
                            placeholder='city',
                            )
    if city_input:
        search_city(city_input)

@st.fragment
def main():
    data = st.session_state.weather_data[st.session_state.week_day]
    with st.container(horizontal_alignment='right', vertical_alignment='center'):
        st.toggle(label='°F', value=st.session_state.fahrenheit, key='fahrenheit')

    temp_unit = '°F' if st.session_state.fahrenheit else '°C'
    temp_col  ='temperature_f' if st.session_state.fahrenheit else 'temperature'
    temp_diff = st.session_state.temp_diff_f if st.session_state.fahrenheit else st.session_state.temp_diff
    chart_get_idx = st.session_state.get('chart_click', {}).get('selection', {}).get('points')
    data_idx = 0
    show_delta = False    
    first_day = next(iter(st.session_state.weather_data))

    if st.session_state.new_data:
            metric_text = f'{data["weather_emoji"][data_idx]} {data[temp_col][data_idx]} {temp_unit}'
            aux_text = f'{st.session_state.week_day}, {data["time"][data_idx]}<br>{data["weather_text"][data_idx]}'
            show_delta = (
                temp_diff != 0
                and data_idx == 0
                and first_day == st.session_state.week_day
            )
    else:
        if (st.session_state.force_default or not chart_get_idx) and first_day == st.session_state.week_day:
            data_idx = 0
            metric_text = f'{data["weather_emoji"][data_idx]} {data[temp_col][data_idx]} {temp_unit}'
            aux_text = f'{st.session_state.week_day}, {data["time"][data_idx]}<br>{data["weather_text"][data_idx]}'
            show_delta = temp_diff != 0 and data_idx == 0
        elif (st.session_state.force_default or not chart_get_idx):
            aux_idx = data[temp_col].idxmax()
            metric_text = f'{data["weather_emoji"][aux_idx]} {data[temp_col][aux_idx]} {temp_unit}'
            aux_text = f'{st.session_state.week_day}<br>{data["weather_text"].value_counts().idxmax()}'
        else:
            data_idx = chart_get_idx[0]["point_index"]
            metric_text = f'{data["weather_emoji"][data_idx]} {data[temp_col][data_idx]} {temp_unit}'
            aux_text = f'{st.session_state.week_day}, {data["time"][data_idx]}<br>{data["weather_text"][data_idx]}'
            show_delta = (
                temp_diff != 0
                and data_idx == 0
                and first_day == st.session_state.week_day
            )

    st.session_state.new_data = False
    st.session_state.force_default = False

    with st.container(horizontal_alignment='center', vertical_alignment='center'):
        subCol1, subCol2 = st.columns(2,vertical_alignment='center')
        with subCol1:
            st.metric(label=st.session_state.current_city, 
                        value=metric_text, 
                        delta= f'{temp_diff} {temp_unit}' if show_delta else None,
                        width='stretch',
                        height=120,
                        )
        with subCol2:
            st.markdown(body=f'**Weather**<br>' + aux_text,
                        text_alignment='right',
                        unsafe_allow_html=True,
                        width='stretch'
                        )
        tab1, tab2, tab3 = st.tabs(['Temperature', 'Rain', 'Wind'])
        with tab1:
            if len(data) > 1:
                fig = temperature_chart(data, 'time', temp_col)
                st.plotly_chart(fig,
                                on_select='rerun', 
                                config={'displayModeBar': False},
                                key='chart_click')
            else:
                with st.container( vertical_alignment='center', height=225):
                     st.markdown(body=f'**No more data for today**',
                        text_alignment='center',
                        unsafe_allow_html=True,
                        )
        with tab2:
            if len(data) > 1:
                fig = rain_chart(data, 'time','precipitation_probability')
                st.plotly_chart(fig, config={'displayModeBar': False}) 
            else:
                with st.container( vertical_alignment='center', height=225):
                    st.markdown(body=f'**No more data for today**',
                    text_alignment='center',
                    unsafe_allow_html=True,
                    )
        with tab3:
            if len(data) > 1:
                fig = wind_chart(data, 'time', 'wind_speed', 'wind_direction', 'wind_acronym')
                st.plotly_chart(fig, config={'displayModeBar': False}) 
            else:
                with st.container( vertical_alignment='center', height=225):
                     st.markdown(body=f'**No more data for today**',
                        text_alignment='center',
                        unsafe_allow_html=True,
                        )
                
        def on_change():
            if st.session_state.week_day is None:
                st.session_state.week_day = st.session_state.week_day_cache
            else:
                st.session_state.force_default = True
                st.session_state.week_day_cache = st.session_state.week_day 
            
        with st.container(horizontal_alignment='center', vertical_alignment='center'):
            st.segmented_control(label='Week Selection',
                        label_visibility='collapsed',
                        options=st.session_state.weather_data,
                        format_func=lambda x: x[:3],
                        selection_mode='single',
                        key='week_day',
                        on_change=on_change
                    )  
    
if st.session_state.current_city:
    main()