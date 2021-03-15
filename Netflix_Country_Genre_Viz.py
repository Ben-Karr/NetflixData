import pandas as pd
import numpy as np

import plotly.graph_objs as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from pathlib import Path

from collections import Counter #Count actors

# Load Data
src_path = Path('data/netflix_titles.csv')
df_src = pd.read_csv(src_path)

# Lists of uniqe countries & genres
unique_countries = list(set(', '.join(df_src.country.fillna('')).split(', ')))
country_options = [{'label': x, 'value': x} for x in unique_countries]

unique_genres = list(set(', '.join(df_src.listed_in).split(', ')))
genre_options = [{'label': x, 'value': x} for x in unique_genres]

# Build Dataframe, contains count of shows for every country by every genre
# Build Dataframe, contains count of shows for every country by every genre
def country_by_genre(df
                    ,keep_features = ['show_id','title','country','listed_in','rating']
                    ,keep_countries = ['Germany','Brazil']
                    ,keep_genres = ['Action & Adventure', 'Comedies']
                    ):
    df_tmp = df.copy()

    df_tmp.country = df_tmp.country.fillna('').apply(lambda x: x.split(', '))
    df_tmp.listed_in = df_tmp.listed_in.fillna('').apply(lambda x: x.split(', '))
    
    # pivot country & genre to columns
    df_tmp = df_tmp.explode('country').explode('listed_in')
    df_tmp.reset_index(drop=True, inplace=True)
    
    return df_tmp

def filter_df(df,
              keep_features = ['show_id','title','country','listed_in','rating'],
              keep_countries = ['Germany','Brazil'],
              keep_genres = ['Action & Adventure', 'Comedies'],
              relative = 'abs',
             ):
    df_tmp = df.copy()
   
    df_tmp = df_tmp.groupby(['country', 'listed_in']).size().unstack().fillna(0).astype(int)
    
    if relative == 'rel-country':
        df_tmp = (df_tmp.divide(shows_per_country, axis = 0) * 100).round(2)
    elif relative == 'rel-genre':
        df_tmp = (df_tmp.divide(shows_per_genre, axis = 1) * 100).round(2)
    
    df_tmp = df_tmp.loc[keep_countries, keep_genres]
    
    return df_tmp

def get_heatmap(df):
    trace0 = go.Heatmap(
    x = df.columns.tolist(),
    y = df.index.values.tolist(),
    z = df.values
    )

    data = [trace0]


    layout = go.Layout(
        title = 'Number of shows per Country by Genre'
    )

    return data, layout

def get_stacked_bar(df, stacked = True):
    data = [go.Bar(
        x = df.index.tolist(),
        y = df[genre].tolist(),
        name = genre
    ) for genre in df.columns.tolist()]

    layout = go.Layout(
        title = 'Number of shows per Country by Genre',
    )

    if stacked:
        layout['barmode'] = 'stack'

    return data, layout

## Initial:
df = country_by_genre(df_src)
shows_per_country = df.groupby(['country'])['title'].nunique().to_frame().sort_values(['country']).values
shows_per_genre = df.groupby(['listed_in'])['title'].nunique().to_frame().sort_values(['listed_in']).title.values
df = filter_df(df)

data, layout = get_stacked_bar(df)
print('Hello')
print(type(data), type(layout))

## Start App
app = dash.Dash()

app.layout = html.Div([
    html.Div([
        html.H3('Pick the countries you are interested in:'),
        dcc.Dropdown(
            id = 'country-dropdown',
            options = country_options,
            value = ['Germany','Brazil', 'United States'],
            multi = True
        )
    ]),
    html.Div([
        html.H3('Pick the genres you are interested in:'),
        dcc.Dropdown(
            id = 'genre-dropdown',
            options = genre_options,
            value = ['Action & Adventure', 'Comedies'],
            multi = True
        )
    ]),
    html.Div([
        html.H3('Choose a visualization'),
        dcc.RadioItems(
            id = 'viz-radio',
            options = [
                {'label': 'Heatmap', 'value': 'heat'},
                {'label': 'Stacked Barchart', 'value': 'stacked'},
                {'label': 'Grouped Barchart', 'value': 'grouped'},                
            ],
            value = 'heat'
        )
    ]),
    html.Div([
        html.H3('Absolute number of shows or percentage'),
        dcc.RadioItems(
            id = 'rel-radio',
            options = [
                {'label': 'Absolute', 'value': 'abs'},
                {'label': 'Percentage by country', 'value': 'rel-country'},
                {'label': 'Percentage by genre', 'value': 'rel-genre'},   
            ],
            value = 'abs'
        )
    ]),
    dcc.Graph(
        id = 'content-graph',
        figure = dict(
            data = data,
            layout = layout
        )
    )
])

@app.callback(
    Output('content-graph','figure'),
    [Input('country-dropdown','value'),
     Input('genre-dropdown', 'value'),
     Input('viz-radio','value'),
     Input('rel-radio','value')]
)
def update_content(country_choices, genre_choices, viz_choice, rel_choice):

    df = country_by_genre(df_src)

    df = filter_df(
              df,
              keep_countries = country_choices,
              keep_genres = genre_choices,
              relative = rel_choice
              )
    print(df)

    if viz_choice == 'heat':
        data, layout = get_heatmap(df)
    else:
        if viz_choice == 'stacked':
            stacked = True
        else:
            stacked = False
        data, layout = get_stacked_bar(df, stacked)

    fig = dict(
        data = data,
        layout = layout
    )

    return fig

if __name__ == '__main__':
    app.run_server()