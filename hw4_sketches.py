#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 24 21:09:15 2021

@author: bonzilla
"""


# %% ENVIRONMENT

import pandas as pd
import numpy as np
import folium
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from folium.plugins import MarkerCluster

#references
# 1) https://towardsdatascience.com/visualizing-data-at-the-zip-code-level-with-folium-d07ac983db20
# 2) https://data.beta.nyc/dataset/nyc-zip-code-tabulation-areas


# %% DATA IMPORT

url = 'https://raw.githubusercontent.com/SmilodonCub/DATA608/master/tree_dat_4Qs.csv'
tree_dat = pd.read_csv( url )
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
    tick_placement = [ sum(val)/2 for val in ranges ]
    tick_labels = [ str( round( val[1]-val[0],1 ))+'%' for val in ranges ]
    needle_dir = needle_dir*180/100 #rescale from 0-100 to 0-180
    needle_dir = 180-needle_dir #flip axis direction
    return needle_dir, maxidx, tick_placement, tick_labels

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
    boro_nd, maxidx, ticks, labels = needle_dir( boro_health_counts['percent'] )
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
        'axis': {'range': [None, 100], 'tickwidth': 3, 'tickcolor': "gray", 
                 'tickfont': { 'size':15}, 'tickvals': ticks, 'ticktext': labels,
                 'tickangle': 0},
        'bgcolor': "white",
        'borderwidth': 4,
        'bordercolor': "gray",
        'steps': steps_list,
    }))

    fig.update_layout(paper_bgcolor = "cornsilk", font = {'color': "gray", 'family': "Arial"},
                      xaxis={'showgrid': False, 'range':[-1,1], 'showticklabels':False},
                      yaxis={'showgrid': False, 'range':[0,1], 'showticklabels':False},
                      plot_bgcolor='rgba(0,0,0,0)')

    theta = boro_nd
    r= 0.6
    x_head = r * np.cos(np.radians(theta))
    y_head = r * np.sin(np.radians(theta))

    fig.add_annotation( ax=0, ay=0, axref='x', ayref='y', x=x_head, y=y_head,
                       xref='x', yref='y', showarrow=True, arrowhead=3, 
                       arrowsize=2, arrowwidth=4, arrowcolor = colors[maxidx] )
    
    return fig

def draw_dial_legend():
    # draw simple legend for dial plots
    fig = go.Figure()
    # Create scatter trace of text labels
    fig.add_trace(go.Scatter(
        x=[15, 15, 15],
        y=[4, 12, 20],
        text=["Poor","Fair","Good"],
        mode="text" ))
    # Set axes properties
    fig.update_xaxes(range=[0, 24])
    fig.update_yaxes(range=[0, 24])
    # Add shapes
    fig.add_shape(type="rect",
                  xref="paper", yref="paper",
                  x0=3/12, y0=1/12,
                  x1=5/12, y1=3/12,
                  line=dict(color="gray",width=3),
                  fillcolor='gold')
    fig.add_shape(type="rect",
                  xref="paper", yref="paper",
                  x0=3/12, y0=5/12,
                  x1=5/12, y1=7/12,
                  line=dict(color="gray",width=3),
                  fillcolor='greenyellow')
    fig.add_shape(type="rect",
                  xref="paper", yref="paper",
                  x0=3/12, y0=9/12,
                  x1=5/12, y1=11/12,
                  line=dict(color="gray",width=3),
                  fillcolor='forestgreen')
    fig.update_layout(paper_bgcolor = "cornsilk", font = {'color': "gray", 'family': "Arial", 'size':36},
                      xaxis={'showgrid': False, 'showticklabels':False},
                      yaxis={'showgrid': False, 'showticklabels':False},
                      plot_bgcolor='rgba(0,0,0,0)')
    return fig

# choropleth map of trees per selected species
def map_certain_trees( df_species ):
    NY_coords = [ 40.7128, -74.0060 ]
    ny_map = folium.Map( location = NY_coords, tiles = 'Stamen Watercolor', zoom_start = 10 )
    health_class = [ 'Poor', 'Fair', 'Good' ]
    class_color = [ 'orange', 'lightgreen', 'green' ]
    marker_cluster = MarkerCluster().add_to( ny_map )
    for num,hclass in enumerate(health_class):
        df_species_class = df_species[ df_species[ 'health' ] == hclass ]
        for idx, row in df_species_class.iterrows():
            folium.Marker( location = [row['latitude'], row['longitude']],
                                        icon=folium.Icon(color=class_color[num], 
                                        icon='tree', prefix='fa')).add_to( marker_cluster )
    ny_map.save( 'nycmap.html' )
    

def steward_impact_data( df_species ):
    #helper function to clean data
    
    #get counts grouped by boro, health & stewards
    df_stewards = df_species.groupby(['boroname', 'health']).steward.value_counts()
    df_stewards.name = 'steward_x_health_counts'
    df_stewards = df_stewards.reset_index()
    #get counts grouped by boro & steward
    df_healthbn = df_species.groupby(['boroname']).steward.value_counts()
    df_healthbn.name = 'steward_counts'
    df_healthbn.reset_index()
    #merge counts
    df_stewards = df_stewards.merge( df_healthbn, on = ['boroname', 'steward'])
    df_stewards['stewards_percent'] = round( 100*df_stewards['steward_x_health_counts']/df_stewards['steward_counts'],2 )
    df_stewards.steward = pd.Categorical(df_stewards.steward, 
                      categories=["None","1or2","3or4","4orMore"],
                      ordered=True)
    df_stewards = df_stewards.sort_values( ['steward', 'health']).reset_index()
    return df_stewards

def steward_impact_plot( df_steward ):
    fig = go.Figure()

    fig.update_layout(
        template="simple_white",
        title = 'Relative Proportion of Trees in Good Health',
        title_x=0.5,
        xaxis=dict(title_text="Number of Stewards grouped by NYC Borough"),
        yaxis=dict(title_text="%"),
        barmode="stack",
        paper_bgcolor = "cornsilk", 
        font = {'color': "gray", 'family': "Arial", 'size':18},
        plot_bgcolor='rgba(0,0,0,0)')

    colors = ["gold", "greenyellow", "forestgreen"]
    health_lev = ['Poor', 'Fair', 'Good']

    for r, c in zip(health_lev, colors):
        plot_df = df_steward[df_steward['health'] == r]
        fig.add_trace( go.Bar(x=[plot_df.boroname, plot_df.steward], 
                              y=plot_df.stewards_percent, name=r, marker_color=c) )
    return fig

def steward_numerosity_plot( df_steward ):
    fig = go.Figure()

    fig.update_layout(
        template="simple_white",
        title = 'Numerosity of Trees',
        title_x=0.5,
        xaxis=dict(title_text="Number of Stewards grouped by NYC Borough"),
        yaxis=dict(title_text="Count"),
        barmode="stack",
        paper_bgcolor = "cornsilk", 
        font = {'color': "gray", 'family': "Arial", 'size':18},
        plot_bgcolor='rgba(0,0,0,0)')

    colors = ["gold", "greenyellow", "forestgreen"]
    health_lev = ['Poor', 'Fair', 'Good']

    for r, c in zip(health_lev, colors):
        plot_df = df_steward[df_steward['health'] == r]
        fig.add_trace( go.Bar(x=[plot_df.boroname, plot_df.steward], 
                              y=plot_df.steward_x_health_counts, name=r, marker_color=c) )
    return fig

# %% formating NYC geojson data

app = dash.Dash(__name__)

df = tree_dat_4Qs.dropna()
dfff = tree_dat_4Qs[ tree_dat_4Qs[ 'spc_common' ] == 'crimson king maple' ]
available_species = np.sort( df['spc_common'].unique() ) 
available_health = df['health'].unique()
map_certain_trees( dfff )
health_dictionary ={'Poor' : 1, 'Fair' : 2, 'Good' : 3}
color_dictionary ={'Poor' : 'gold', 'Fair' : 'greenyellow', 'Good' : 'forestgreen'}
boro_health_counts = find_boro_health_counts( dfff, color_dictionary, health_dictionary )
fig_man = draw_boro_dial( boro_health_counts, 'Manhattan' )
fig_bkln = draw_boro_dial( boro_health_counts, 'Brooklyn' )
fig_qns = draw_boro_dial( boro_health_counts, 'Queens' )
fig_brnx = draw_boro_dial( boro_health_counts, 'Bronx' )
fig_si = draw_boro_dial( boro_health_counts, 'Staten Island' )
dial_legend = draw_dial_legend()
steward_dat = steward_impact_data( dfff )
fig_steward = steward_impact_plot( steward_dat )
fig_steward2 = steward_numerosity_plot( steward_dat )



app.layout = html.Div([
    html.Div(
        html.Img(src=app.get_asset_url('nyctree1.png'), 
                 style={'height':'40%', 'width':'40%'}), 
        style={'textAlign': 'center'}
        ),
    html.H1('Tree Health Applet for NYC', style={'color': 'green', 'fontSize': 40, 'textAlign': 'center'}),
    html.Div([
        html.P('Welcome arborists & tree enthusiasts!',style={'fontSize': 20, 'textAlign': 'center'}),
        html.P("This tiny applet will enhance your understanding tree health in NYC. Just pick a tree species of interest from the dropdown menu to the left and explore the visualization panels",
               style={'fontSize': 20, 'textAlign': 'center'})
    ]),    
    
    html.Div([
            dcc.Dropdown(
                id='tree_species',
                options=[{'label': i, 'value': i} for i in available_species],
                value='crimson king maple'
            )
        ], style={'width': '25%', 'height':'5%', 'display': 'inline-block'}),
    
    dcc.Tabs([
        dcc.Tab( label = 'Health Dial', children= [
            html.H2('Borough Health Dials', style={'color': 'green', 'fontSize': 30, 'textAlign': 'center'}),
            html.P('Each dial shows the proportions of trees for the selected tree species that are in Good, Fair or Poor health for each NYC borough. The arrows point to and are colored the same as the majority health label.',
                   style={'fontSize': 20, 'textAlign': 'center'}),
            html.Div([
                # row for static boro dial plots
                html.Div([
                    dcc.Graph(
                        id='graph1',
                        figure=fig_man
                        )], 
                    style={'width': '32%', 'height': '32%' , 
                           'display': 'inline-block','margin' : '1px 1px 1px 1px'}),
                
                html.Div([
                    dcc.Graph(
                        id='graph2',
                        figure=fig_bkln
                        )], 
                    style={'width': '32%', 'height': '32%' , 
                           'display': 'inline-block','margin' : '1px 1px 1px 1px'}),
                
                html.Div([
                    dcc.Graph(
                        id='graph3',
                        figure=fig_qns
                        )], 
                    style={'width': '32%', 'height': '32%' , 
                           'display': 'inline-block','margin' : '1px 1px 1px 1px'}),
                ], className='row'),
            
            html.Div([
                html.Div([
                    dcc.Graph(
                        id='graph4',
                        figure=fig_brnx
                        )], 
                    style={'width': '32%', 'display': 'inline-block', 
                           'margin' : '1px 1px 1px 1px'}),
            
                html.Div([
                    dcc.Graph(
                        id='graph5',
                        figure=fig_si
                        )], 
                    style={'width': '32%', 'display': 'inline-block',
                           'margin' : '1px 1px 1px 1px'}),
                
                html.Div([
                    dcc.Graph(
                        id='graph6',
                        figure=dial_legend
                        )], 
                    style={'width': '32%', 'display': 'inline-block',
                           'margin' : '1px 1px 1px 1px'}),                
                ], className='row')
            ]),
                     
            dcc.Tab( label = 'City View', children = [
                html.H2('Street-level Tree Health', style={'color': 'green', 'fontSize': 30, 'textAlign': 'center'}),
                html.P('Zoom in to find the health of the selected tree species in your very own neighborhood!',
                       style={'fontSize': 20, 'textAlign': 'center'}),
                html.Div([
                    # map plot. zoom in to see tree health in a certain location
                    html.Iframe( id = 'map', srcDoc = open('nycmap.html', 'r').read(), width = '100%', height='600')
                    ])
                ]),
            
            dcc.Tab( label = 'Steward Impact', children = [
                html.Div([
                    html.H2('Impact of Stewards Tree Health in NYC', style={'color': 'green', 'fontSize': 30, 'textAlign': 'center'}),
                    html.P('Here you can see the Percentage of trees with and without stewards to get a sense of whether stewards have an impact on the health of a species of tree across the boroughs.',
                           style={'fontSize': 20, 'textAlign': 'center'}),
                    dcc.Graph(
                        id='graph7',
                        figure=fig_steward
                        )], 
                    style={'width': '100%', 'height': '100%', 'display': 'inline-block', 
                                           'margin' : '10px 10px 10px 10px'}),                
                html.Div([
                    html.P('Put the figure above in perspective by exploring the relative numerosity of trees in each category.',
                           style={'fontSize': 20, 'textAlign': 'center'}),
                    dcc.Graph(
                        id='graph8',
                        figure=fig_steward2
                        )], 
                    style={'width': '100%', 'height': '100%', 'display': 'inline-block', 
                                           'margin' : '10px 10px 10px 10px'}), 
                    ])
                ])
            ])    

    
    
@app.callback(
    Output('map', 'srcDoc'),
    Output('graph1', 'figure'),  
    Output('graph2', 'figure'),
    Output('graph3', 'figure'),
    Output('graph4', 'figure'),
    Output('graph5', 'figure'),
    Output('graph7', 'figure'),
    Output('graph8', 'figure'),    
    Input('tree_species', 'value'))

def update_graph(value):
    
    dff = df[df['spc_common'] == value]
    map_certain_trees( dff )
    health_dictionary ={'Poor' : 1, 'Fair' : 2, 'Good' : 3}
    color_dictionary ={'Poor' : 'gold', 'Fair' : 'greenyellow', 'Good' : 'forestgreen'}
    boro_health_counts = find_boro_health_counts( dff, color_dictionary, health_dictionary )
    fig_man = draw_boro_dial( boro_health_counts, 'Manhattan' )
    fig_bkln = draw_boro_dial( boro_health_counts, 'Brooklyn' )
    fig_qns = draw_boro_dial( boro_health_counts, 'Queens' )
    fig_brnx = draw_boro_dial( boro_health_counts, 'Bronx' )
    fig_si = draw_boro_dial( boro_health_counts, 'Staten Island' )
    steward_dat = steward_impact_data( dff )
    fig_steward = steward_impact_plot( steward_dat )
    fig_steward2 = steward_numerosity_plot( steward_dat )
    return open( 'nycmap.html', 'r').read(), fig_man, fig_bkln, fig_qns, fig_brnx, fig_si, fig_steward, fig_steward2

    


if __name__ == '__main__':
    app.run_server(debug=False)    
    
    