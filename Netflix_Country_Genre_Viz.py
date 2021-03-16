import pandas as pd
import numpy as np

import plotly.graph_objs as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from pathlib import Path


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

    data = [go.Heatmap(
        x = df.columns.tolist(),
        y = df.index.values.tolist(),
        z = df.values,
        colorscale = 'Jet'
        )
    ]

    layout = go.Layout(
        title = 'Number of shows per Country by Genre',
        plot_bgcolor = 'rgb(56,56,56)',
        paper_bgcolor = 'rgb(56,56,56)',
        font = dict(
            color = 'white'
        ),
        margin = dict(
            l = 100,
            pad = 0
        )
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
        plot_bgcolor = 'rgb(56,56,56)',
        paper_bgcolor = 'rgb(56,56,56)',     
        font = dict(
            color = 'white'
        )        
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


## Start App
app = dash.Dash(__name__)

#app.css.config.serve_locally = True
#app.scripts.config.serve_locally = True

app.layout = html.Div(
    children = [
        html.Div(
            dcc.Markdown('''## Netflix Data Visualization'''),
            style = dict(
                textAlign = 'center',
                color = 'red'
                )
        ),
        html.Hr(),
        html.Div(
            className = 'content',
            children = [
                dcc.Markdown(
                    ''' ### Select Countries '''
                    ),
                dcc.Markdown(
                    ''' Pick the countries you are interested in. 
                    Choose from a list or search for the country name to 
                    add to the list, remove from the list by clicking the `x`.
                    '''
                    ),
                dcc.Dropdown(
                    id = 'country-dropdown',
                    options = country_options,
                    className = 'dropdown-group',
                    value = ['Germany','Brazil', 'United States'],
                    multi = True
                    ),
                dcc.Markdown(
                    ''' ### Select Genres '''
                    ),
                dcc.Markdown(
                    '''Pick the genres you are interested in. Choose from 
                    a list or search for the genre name to add to the list, 
                    remove from the list by clicking the `x`.''',
                    ),
                dcc.Dropdown(
                    id = 'genre-dropdown',
                    options = genre_options,
                    value = ['Action & Adventure', 'Comedies'],
                    multi = True
                    ),
                dcc.Markdown(
                    ''' ### Select visualization''',
                    ),
                dcc.RadioItems(
                    id = 'viz-radio',
                    options = [
                        {'label': 'Heatmap', 'value': 'heat'},
                        {'label': 'Stacked Barchart', 'value': 'stacked'},
                        {'label': 'Grouped Barchart', 'value': 'grouped'},                
                        ],
                    value = 'heat',
                    labelStyle = {'display': 'block'}
                    ),
                dcc.Markdown(
                    ''' ### Select presentation '''
                    ),
                dcc.Markdown(
                    '''Pick if you want the absolute or relative values. 
                    "Percentage by country" divides the number of shows for a 
                    particular genre and country by the total number of shows in that country. 
                    "Percentage by genre" divides the number of shows for a particular genre 
                    and country by the total number of shows for that genre. This might be confusing in 
                    combination with a bar chart.''',
                    ),
                dcc.RadioItems(
                    id = 'rel-radio',
                    options = [
                        {'label': 'Absolute', 'value': 'abs'},
                        {'label': 'Percentage by country', 'value': 'rel-country'},
                        {'label': 'Percentage by genre', 'value': 'rel-genre'},   
                        ],
                    value = 'abs',
                    labelStyle = {'display': 'block'}
                    )
                ],
            style = dict(
                width = '18%', 
                float = 'left',
                fontSize = 12
                )
            ),
        html.Div(
            className = 'content',
            children = [
                dcc.Graph(
                    id = 'content-graph',
                    figure = dict(
                        data = data,
                        layout = layout,
                        )
                    )
                ], 
            style = dict(
                width = '80%',
                float = 'right',
                )
            )
        ],
    )

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
    app.run_server(debug = True)