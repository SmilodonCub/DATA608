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
import plotly.graph_objects as go
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



# %% functions to build app plots

# needle direction (helper for draw_boro_dial)
def needle_dir( boro_prop ):
    num_rows = boro_prop.shape[0]
    if num_rows == 3:
        ranges = [ [0, boro_prop[0]], 
             [boro_prop[0], boro_prop[0] + boro_prop[1]],
             [boro_prop[0] + boro_prop[1], boro_prop[0] + boro_prop[1] + boro_prop[2]]]
    elif num_rows == 2:
        ranges = [ [0, boro_prop[0]], 
             [boro_prop[0], boro_prop[0] + boro_prop[1]]]
    elif num_rows == 1:
        ranges = [ [0, boro_prop[0]]]
    maxidx = boro_prop.idxmax()
    needle_dir = sum( ranges[maxidx] )/2
    needle_dir = needle_dir*180/100 #rescale from 0-100 to 0-180
    needle_dir = 180-needle_dir #flip axis direction
    return needle_dir, maxidx

# functionaliza boro_health_counts
def find_boro_health_counts( df_species, color_dictionary, health_dictionary ):
    # find counts
    boro_health_counts = df_species.groupby( ['boroname', 'health'] ).size().reset_index(name='counts_health')
    boro_species_counts = df_species.groupby( ['boroname'] ).size().reset_index(name='counts_species')
    boro_health_counts = boro_health_counts.merge( boro_species_counts, on = 'boroname' )
    boro_health_counts['percent'] = boro_health_counts['counts_health']/boro_health_counts['counts_species']*100
    boro_health_counts['rank_health'] = boro_health_counts['health'].map( health_dictionary )
    boro_health_counts['color_health'] = boro_health_counts['health'].map( color_dictionary )
    boro_health_counts = boro_health_counts.sort_values( by = ['boroname','rank_health'] ).reset_index()
    return boro_health_counts


# dial plots to indicate tree health in each borough
def draw_boro_dial( boro_health_counts, boro ):
    boro_health_counts = boro_health_counts[ boro_health_counts['boroname'] == boro ].reset_index()
    num_ranks = boro_health_counts.shape[0]
    colors = boro_health_counts['color_health']
    if num_ranks == 3:
        steps_list = [
            {'range': [0, boro_health_counts['percent'][0]], 'color': colors[0]},
            {'range': [boro_health_counts['percent'][0], boro_health_counts['percent'][0] + boro_health_counts['percent'][1]], 
             'color': colors[1]},
            {'range': [boro_health_counts['percent'][0] + boro_health_counts['percent'][1], 
                        boro_health_counts['percent'][0] + boro_health_counts['percent'][1] + boro_health_counts['percent'][2]], 
             'color': colors[2]}]
    elif num_ranks == 2:
        steps_list = [
            {'range': [0, boro_health_counts['percent'][0]], 'color': colors[0]},
            {'range': [boro_health_counts['percent'][0], boro_health_counts['percent'][0] + boro_health_counts['percent'][1]], 
             'color': colors[1]}]
    elif num_ranks == 1:
        steps_list = [
            {'range': [0, boro_health_counts['percent'][0]], 'color': colors[0]}]
    fig = go.Figure(go.Indicator(
    mode = "gauge",
    #value = 0,
    domain = {'x': [0, 1], 'y': [0, 1]},
    title = {'text': boro, 'font': {'size': 36}},     
    gauge = {
        'axis': {'range': [None, 100], 'tickwidth': 3, 'tickcolor': "gray", 'tickfont': { 'size':20}},
        'bgcolor': "white",
        'borderwidth': 4,
        'bordercolor': "gray",
        'steps': steps_list,
    }))

    fig.update_layout(paper_bgcolor = "cornsilk", font = {'color': "gray", 'family': "Arial"},
                      xaxis={'showgrid': False, 'range':[-1,1], 'showticklabels':False},
                      yaxis={'showgrid': False, 'range':[0,1], 'showticklabels':False},
                      plot_bgcolor='rgba(0,0,0,0)')

    boro_percent = boro_health_counts['percent']
    boro_nd, maxidx = needle_dir( boro_percent )
    theta = boro_nd
    r= 0.6
    x_head = r * np.cos(np.radians(theta))
    y_head = r * np.sin(np.radians(theta))

    fig.add_annotation( ax=0, ay=0, axref='x', ayref='y', x=x_head, y=y_head,
                       xref='x', yref='y', showarrow=True, arrowhead=3, 
                       arrowsize=2, arrowwidth=4, arrowcolor = colors[maxidx] )
    
    return fig

# choropleth map of trees per selected species
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
health_dictionary ={'Poor' : 1, 'Fair' : 2, 'Good' : 3}
color_dictionary ={'Poor' : 'gold', 'Fair' : 'greenyellow', 'Good' : 'forestgreen'}
boro_health_counts = find_boro_health_counts( dfff, color_dictionary, health_dictionary )
fig = draw_boro_dial( boro_health_counts, 'Queens' )



app.layout = html.Div([
    html.Div(
        html.Img(src=app.get_asset_url('nyctree1.png'), style={'height':'60%', 'width':'60%'}), style={'textAlign': 'center'}
        ),
    html.H1('Tree Health NYC'),
    

    html.Div([
        # row for static boro dial plots
        html.Div([
            dcc.Graph(
                id='graph1',
                figure=fig
            )], style={'width': '32%', 'display': 'inline-block', 'padding': '0 20'}),
        
        html.Div([
            dcc.Graph(
                id='graph2',
                figure=fig
            )], style={'width': '32%', 'display': 'inline-block', 'padding': '0 20'}),
        
        html.Div([
            dcc.Graph(
                id='graph3',
                figure=fig
            )], style={'width': '32%', 'display': 'inline-block'}),
        
    ], className='row'),        


    html.Div([        
        html.Div([
            dcc.Graph(
                id='graph4',
                figure=fig
            )], style={'width': '32%', 'display': 'inline-block', 'margin-left' : '300px'}),
        
        html.Div([
            dcc.Graph(
                id='graph5',
                figure=fig
            )], style={'width': '32%', 'display': 'inline-block', 'padding': '0 0'}),
                           
    ], className='row'),
                     
                     
    html.Div([
        # map plot. zoom in to see tree health in a certain location

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
    
    