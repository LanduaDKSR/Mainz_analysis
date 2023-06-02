import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from streamlit_keplergl import keplergl_static
from keplergl import KeplerGl
from geojson import LineString as geoLS
import ast
import folium
from streamlit_folium import st_folium
import math
from PIL import Image
import altair as alt
import markt_config

from functions import trip_layer, point_of_interest

st.set_page_config(layout="wide")

image = Image.open('Logo.png')
config = markt_config.config

header1, header2 = st.columns([3,1])
with header1:
    st.write("""
    # MAINZ MARKTFRÜHSTÜCK
    ### Point-of-Interest-Analyse
    """)

with header2:
    st.image(image)


@st.cache_data
def load_data():
    df = pd.read_csv('Markt_Tag.csv')
    df['coordinates'] = df['coordinates'].apply(lambda x: ast.literal_eval(x))
    df['timestamps_list'] = df['timestamps_list'].apply(lambda x: ast.literal_eval(x))
    df['geo_json'] = trip_layer(df)
    return df


df=load_data()

Markt = [8.2749, 49.9993]
colors = ["#FFED00", "#C00000", "#164194", "#3E7A48"]

col1, col2 = st.columns([2,3])
with col1:
    radius = st.slider('Radius', 0, 1000, 200, 50)
    #radius = 400
    df['Markt'] = df['coordinates'].apply(lambda x: point_of_interest(x,point=Markt,radius=radius))
    map_point = pd.DataFrame({'Name': ['Mainzer Marktfrühstück'], 'lon': [Markt[0]], 'lat': [Markt[1]], 'Radius': radius})

    # Gesamtverteilung
    base = alt.Chart(df).encode(
                    x=('count(Markt):Q'),
                    y='Markt',
                    color=alt.Color('Markt:N', scale=alt.Scale(range=colors)),
                    tooltip=[alt.Tooltip('count():Q', title='Anzahl Fahrten')]
                ).properties(height=300)
    fig = base.mark_bar() + base.mark_text(align='left',dx=2)
    st.altair_chart(fig, theme="streamlit", use_container_width=True)


    # Stundenübersicht
    fig_2 = alt.Chart(df).mark_bar(size=14, opacity=0.8).encode(
            x='hour',
            y='count(hour)',
            color=alt.Color('Markt:N', scale=alt.Scale(range=colors), legend=None),
            order=alt.Order('Markt'),
            tooltip=[alt.Tooltip('hour:Q', title='Uhrzeit'), alt.Tooltip('count():Q', title='Anzahl Fahrten')])
    st.altair_chart(fig_2, theme="streamlit", use_container_width=True)


with col2:
    col21, col22 = st.columns([1,1])
    with col21:
        # Anzahl nach Kategorie
        nearest = alt.selection(type='single', nearest=True, on='mouseover',
                        fields=['hour'], empty='none')

        # The basic line
        line = alt.Chart(df).mark_line().encode(
            x='hour:Q',
            y='count(hour):Q',
            color=alt.Color('Markt:N', scale=alt.Scale(range=colors), legend=None))

        selectors = alt.Chart(df).mark_point().encode(
            x='hour:Q',
            opacity=alt.value(0),
        ).add_selection(nearest)

        # Draw points on the line, and highlight based on selection
        points = line.mark_point().encode(
            opacity=alt.condition(nearest, alt.value(1), alt.value(0)))

        # Draw text labels near the points, and highlight based on selection
        text = line.mark_text(align='left', dx=5, dy=-5).encode(
            text=alt.condition(nearest, 'count(hour):Q', alt.value(' ')))

        # Draw a rule at the location of the selection
        rules = alt.Chart(df).mark_rule(color='gray').encode(
            x='hour:Q').transform_filter(nearest)

        fig_3 = alt.layer(line, selectors, points, rules, text).properties(height=250)
        st.altair_chart(fig_3, theme="streamlit", use_container_width=True) 

    with col22:
        map = folium.Map(location=[Markt[1], Markt[0]], zoom_start=14)
        folium.Circle([Markt[1], Markt[0]],
                            radius=radius,
                            tooltip="Markt-Umkreis",
                            fill=True,
                            color="purple"
                        ).add_to(map)
        folium.Marker([Markt[1], Markt[0]],
                    tooltip="Markt").add_to(map)

        st_data = st_folium(map, height=250, width=250)

    map_2 = KeplerGl(height=500, data={'Scooter': df, 'Markt': map_point}, config=config)
    keplergl_static(map_2)

#st.dataframe(df)
