import pandas as pd
import numpy as np
from pandas import to_datetime
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pydeck as pdk
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
import urllib.error

st.set_page_config(page_title='Historical Buoy Data App v0.2')
st.title('Historic Buoy Data App')

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')

driver = Chrome(chrome_options=chrome_options)

# starting data
data = pd.DataFrame({
    'id' : ['41043', '42060', '44017', '51101'],
    'buoy' : ['Station 41043 - NE PUERTO RICO - 170 NM NNE of San Juan, PR', 
            'Station 42060 - Caribbean Valley - 63 NM WSW of Montserrat',
            'Station 44017 (LLNR 665) - MONTAUK POINT - 23 NM SSW of Montauk Point, NY',
            'Station 51101 (LLNR 28006.3) - NORTHWESTERN HAWAII TWO - 186 NM NW of Kauai Is., HI'
    ],
    'lat' : [21.030, 16.433000, 40.693, 24.361],
    'lon' : [-64.790, -63.331000, -72.049, 162.075]
})

year_list = []
for i in range(2010, 2021):
    year_list.append(str(i))

# create sidebars
buoy = st.sidebar.selectbox("Select buoy", data['id'])
user_input = st.sidebar.text_input("(Alternate) Enter Station ID:")
date_range = st.sidebar.slider("Year range", 2010, 2020, (2019, 2020))
month_range = st.sidebar.slider("Month range", 1, 12, (1, 12))
wave_height = st.sidebar.slider("Swell height", 0, 30, (5, 10))
dpd = st.sidebar.slider('Swell period', 0, 30, (8,20))
dir = st.sidebar.slider("Swell direction", 0, 360, (0, 90))

def degrees_to_cardinal(d):
    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    ix = round(d / (360. / len(dirs)))
    return dirs[ix % len(dirs)]

@st.cache(suppress_st_warning=True)
def loadData():
        if user_input:
            df = pd.DataFrame()
            missing_years = []
            for year in year_list:
                try:
                    buoy_url = 'https://www.ndbc.noaa.gov/view_text_file.php?filename={}h{}.txt.gz&dir=data/historical/stdmet/'.format(user_input, year)
                    df2 = pd.read_table(buoy_url, names=['year', 'month', 'day', 'wave_height'], na_values=[], keep_default_na=False, dtype=str)
                    # drop header rows
                    df2 = df2.iloc[3: , :]
                    df = df.append(df2)
                except:
                    print('Missing data for year ' + year)
                    missing_years.append(str(year))
            df['dir'] = df['year'].str[49:52]
            df['dpd'] = df['year'].str[37:42]
            df['wave_height'] = df['year'].str[32:36]
            df['day'] = df['year'].str[8:10]
            df['month'] = df['year'].str[5:7]
            df['year'] = df['year'].str[:4]

            df['wave_height'].replace('', np.nan, inplace=True)
            df['date'] = df['year'] + '-' + df['month'] + '-' +  df['day']

            # remove no direction rows
            df = df[df['dir'] != '999']

            # drop duplicates
            df = df.drop_duplicates(subset=['date'])
            df['year'] = pd.to_numeric(df['year'])
            df['month'] = pd.to_numeric(df['month'])
            df['date'] = to_datetime(df['date'])
            df['dpd'] = pd.to_numeric(df['dpd'])
            df['wave_height'] = pd.to_numeric(df['wave_height'])
            df['wave_height'] = df['wave_height'] * 3.281
            df['dir'] = pd.to_numeric(df['dir'])
            df = df.sort_values(by=['date'])

            url = 'https://www.ndbc.noaa.gov/station_page.php?station={}'.format(user_input)
            # create Selenium Chrome browser
            driver.get(url)
            lat = driver.execute_script('return currentstnlat')
            lon = driver.execute_script('return currentstnlng')
            midpoint = (np.average(lat), np.average(lon))
            buoy_elem = driver.find_element(By.XPATH, '/html/body/div[2]/table/tbody/tr/td[2]/h1')
            buoy_text = buoy_elem.text
            coords = {'id': [user_input], 'buoy': [buoy], 'lat': [lat], 'lon': [lon]}   
            buoy_point = pd.DataFrame(coords)
            df['lat'] = lat
            df['lon'] = lon
            df['buoy'] = buoy_text
            df['id'] = user_input
            buoy_name = df['buoy'].iloc[0]
            df['cardinal'] = df.apply(lambda x: degrees_to_cardinal(x['dir']), axis = 1)
            return df, midpoint, buoy_point, buoy_name, missing_years
        else:    
            df = pd.DataFrame()
            missing_years = []
            for year in year_list:
                try:
                    buoy_url = 'https://www.ndbc.noaa.gov/view_text_file.php?filename={}h{}.txt.gz&dir=data/historical/stdmet/'.format(buoy, year)
                    df2 = pd.read_table(buoy_url, names=['year', 'month', 'day', 'wave_height'], na_values=[], keep_default_na=False, dtype=str)
                    # drop header rows
                    df2 = df2.iloc[3: , :]
                    df = df.append(df2)
                except:
                    print('Missing data for year ' + year)
                    missing_years.append(str(year))
            df['dir'] = df['year'].str[49:52]
            df['dpd'] = df['year'].str[37:42]
            df['wave_height'] = df['year'].str[32:36]
            df['day'] = df['year'].str[8:10]
            df['month'] = df['year'].str[5:7]
            df['year'] = df['year'].str[:4]

            df['wave_height'].replace('', np.nan, inplace=True)
            df['date'] = df['year'] + '-' + df['month'] + '-' +  df['day']

            # remove no direction rows
            df = df[df['dir'] != '999']

            # drop duplicates
            df = df.drop_duplicates(subset=['date'])
            df['year'] = pd.to_numeric(df['year'])
            df['month'] = pd.to_numeric(df['month'])
            df['date'] = to_datetime(df['date'])
            df['dpd'] = pd.to_numeric(df['dpd'])
            df['wave_height'] = pd.to_numeric(df['wave_height'])
            df['wave_height'] = df['wave_height'] * 3.281
            df['dir'] = pd.to_numeric(df['dir'])
            df = df.sort_values(by=['date'])

            lat = data.loc[data['id'] == buoy, 'lat'].iloc[0]
            lon = data.loc[data['id'] == buoy, 'lon'].iloc[0]

            # Adding code so we can have map default to the center of the data
            midpoint = (np.average(lat), np.average(lon))
            buoy_point = data.loc[data['id'] == buoy]
            buoy_name = data.loc[data['id'] == buoy, 'buoy'].iloc[0]
            df['buoy'] = buoy_name
            df['cardinal'] = df.apply(lambda x: degrees_to_cardinal(x['dir']), axis = 1)
            return df, midpoint, buoy_point, buoy_name, missing_years

try:
    df, midpoint, buoy_point, buoy_name, missing_years = loadData()

    tooltip = {
        "html":
            "<b>ID:</b> {id} <br/>"
            "<b>Name:</b> {buoy} mm<br/>",
        "style": {
            "backgroundColor": "steelblue",
            "color": "black",
        }
    }

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/satellite-v9',
        initial_view_state=pdk.ViewState(
            latitude=midpoint[0],
            longitude=midpoint[1],
            zoom=4,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
            'HexagonLayer',
            data=buoy_point,
            get_position='[lon, lat]',
            radius=200,
            elevation_scale=4,
            elevation_range=[0, 1000],
            pickable=True,
            extruded=True,
            ),
            pdk.Layer(
                'ScatterplotLayer',
                data=buoy_point,
                get_position='[lon, lat]',
                get_color='[200, 30, 0, 160]',
                get_radius=200,
                pickable=True,
                opacity=0.8,
                filled=True,
                radius_scale=3,
                radius_min_pixels=10,
                radius_max_pixels=500
            ),
        ],
        tooltip=tooltip
    ))
    # return the sub-set data  of variables you want to see
    subset_data = df[(df['wave_height'].between(wave_height[0], wave_height[1])) & 
    (df['dir'].between(dir[0], dir[1])) & 
    (df['dpd'].between(dpd[0], dpd[1])) &
    (df['year'].between(date_range[0], date_range[1])) &
    (df['month'].between(month_range[0], month_range[1]))]
    st.header("Selected data for " + buoy_name)
    if missing_years:
        st.caption('Missing data for year(s): ' + ', '.join(missing_years))
    else:
        pass
    st.write(subset_data)

    layout = dict(plot_bgcolor='white',
                margin=dict(t=20, l=20, r=20, b=20),
                xaxis=dict(title='Date',
                            linecolor='#d9d9d9',
                            showgrid=False,
                            mirror=True),
                yaxis=dict(title='Wave Height',
                            linecolor='#d9d9d9',
                            showgrid=False,
                            mirror=True))
    symbols = ['triangle-up', 'triangle-down', 'triangle-right', 'triangle-left', 'triangle-nw', 'triangle-ne', 'triangle-sw', 'triangle-se']
    line_chart= px.scatter(subset_data, x='date', y='wave_height', color='dpd', size='dpd', symbol="cardinal", symbol_map={'N': 'triangle-down', 
                            'NNE': 'triangle-down', 'NNW': 'triangle-down', 'NW': 'triangle-se', 'WNW': 'triangle-se', 'W': 'triangle-right',
                            'WSW': 'triangle-right', 'SW': 'triangle-ne', 'SSW': 'triangle-up', 'S': 'triangle-up', 'SSE': 'triangle-up', 'SE': 'triangle-nw',
                            'ESE': 'triangle-left', 'E': 'triangle-left', 'ENE': 'triangle-left', 'NE': 'triangle-sw'
                            })
    fig= go.Figure(data=line_chart, layout=layout)
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig)
except urllib.error.HTTPError as exception:
    print(exception)
    st.header('No historic data found.')