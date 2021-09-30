#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 24 21:09:15 2021

@author: bonzilla
"""


# %% ENVIRONMENT

import pandas as pd
import numpy as np
import missingno as msno
import json
import folium
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
from folium.plugins import MarkerCluster

#references
# 1) https://towardsdatascience.com/visualizing-data-at-the-zip-code-level-with-folium-d07ac983db20
# 2) https://data.beta.nyc/dataset/nyc-zip-code-tabulation-areas


# %% DATA IMPORT

tree_dat = pd.read_csv( 'trees2015.csv' )
#tree_dat.info()

cols_4Qs = [ 'spc_common', 'boroname', 'health', 'steward', 'zipcode', 'zip_city', 'borocode', 'latitude', 'longitude' ]

tree_dat_4Qs = tree_dat[ cols_4Qs ]
print( tree_dat_4Qs.head() )



# %%
def map_certain_trees( df_species ):
    NY_coords = [ 40.7128, -74.0060 ]
    ny_map = folium.Map( location = NY_coords, tiles = 'Stamen Watercolor', zoom_start = 10 )
    health_class = [ 'Poor', 'Fair', 'Good' ]
    class_color = [ 'red', 'orange', 'green' ]
    marker_cluster = MarkerCluster().add_to( ny_map )
    for num,hclass in enumerate(health_class):
        df_species_class = df_species[ df_species[ 'health' ] == hclass ]
        for idx, row in df_species_class.iterrows():
            folium.Marker( location = [row['latitude'], row['longitude']],
                                        icon=folium.Icon(color=class_color[num], 
                                        icon='tree', prefix='fa')).add_to( marker_cluster )
    ny_map.save( 'nycmap.html' )


# %% formating NYC geojson data

app = dash.Dash(__name__)

df = tree_dat_4Qs
dfff = tree_dat_4Qs[ tree_dat_4Qs[ 'spc_common' ] == 'crepe myrtle' ]
available_species = tree_dat_4Qs['spc_common'].unique()
available_health = tree_dat_4Qs['health'].unique()
map_certain_trees( dfff )

app.layout = html.Div([
    html.Img(src=app.get_asset_url('nyctree1.png')),
    html.H1('Tree Health NYC'),
    html.Div([

        html.Div([
            dcc.Dropdown(
                id='tree_species',
                options=[{'label': i, 'value': i} for i in available_species],
                value='crepe myrtle'
            )
        ], style={'width': '25%', 'display': 'inline-block'}),

        html.Div([
            dcc.Dropdown(
                id='tree_health',
                options=[{'label': i, 'value': i} for i in available_health],
                value='Tree Health'
            )
        ], style={'width': '25%', 'float': 'right', 'display': 'inline-block'})
    ]),
    
    html.Iframe( id = 'map', srcDoc = open('nycmap.html', 'r').read(), width = '100%', height='600')

])
    
    
@app.callback(
    Output('map', 'srcDoc'),
    Input('tree_species', 'value'))

def update_graph(value):
    
    dff = df[df['spc_common'] == value]
    map_certain_trees( dff )
    return open( 'nycmap.html', 'r').read()


if __name__ == '__main__':
    app.run_server(debug=False)    
    
    