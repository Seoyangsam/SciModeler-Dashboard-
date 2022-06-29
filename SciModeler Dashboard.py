#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# SciModeler Dashboard

# Load the libraries
import base64
import os
import signal
from dash.dependencies import Input, Output, State
from dash import Dash, dcc, html, dash_table
import dash
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.express as px
import re
import datetime
import io
from py2neo import Graph
import webbrowser

# Dash is installed and will serve as the primary libary to create the dashboard. 
# Dash is built o top of Plotly.js and React.js
# Dash apps are rendere in the web browser this allows them to be sharred through URL's


# Loading in the data

# Load data directly from Neo4j

# Use py2neo becasue it easy to use
# use the line "! pip install py2neo" if you haven't installed py2neo yet

# Neo4j has to be up and running before connecting python to it
graph = Graph("bolt://localhost:7687", auth=("neo4j", "123")) #auth= should be filled with own username and password

# This is from the sourcecode at https://py2neo.org/2021.1/_modules/py2neo/export.html
# Because the library py2neo.export did not want to work
def to_pandas_data_frame(cursor, index=None, columns=None, dtype=None):
    try:
        # noinspection PyPackageRequirements
        from pandas import DataFrame
    except ImportError:
        warn("Pandas is not installed.")
        raise
    else:
        return DataFrame(list(map(dict, cursor)), index=index, columns=columns, dtype=dtype)


# Steps for data cleaning:
# Step 1. Get from Neo4j: Source -> key -> Abbreviation name of the study -> Make uniquelist with abbreviations
# Create neo_df with function that is made above, just create some dataframe to see if it works
neo_df = to_pandas_data_frame(graph.run("MATCH (n:Source) RETURN n.key"))

unique_articles2 = []
for j in range(len(neo_df)):
    # Make a string of the specific point of data in the list
    string = neo_df.iloc[j,0]
    # Don't worry too much about the '"key":\w{1,}\W', it is just a regular expression to find any string that is behind "key":, consists of sentence characters, is longer than 1 and ends with a none-sentence character
    # If the pattern is not yet in the list unique_articles, it is added
    if re.findall('\w{1,}\W',string) not in unique_articles2:
        unique_articles2.append(''.join(re.findall('(\w{1,})\W',string)))


# Step 2. Create an empty df
# Make list with attributes we want in the df
imp_attributes = ['title', 'doi', 'duration', 'method', 'timing', 'location', 'result',]
main_df = pd.DataFrame(index=unique_articles2, columns = imp_attributes)


# Step 3. Get the right data into the right rows and columns
ann_entities = ["Experiment", "Context", "Treatment", "Intervention", "Platfrom", "Population", "Sample", "Group", "Demographic", "Outcome", "Variable", "Classification", "Source"]
# What we basically do in the next part of code is individually extract every attribute from neo4j
# We check if the key of that attribute is in line with the name of a specific article
# If that is true than we add the value to the right column (attribute) and row (article) in the main_df

# For every annotation entity
for i in range(len(ann_entities)):
    # For every important attribute
    for j in range(len(imp_attributes)):
        # We create a small df for every attribute of an annotation entity, for every of that entity we take the important attribute and the key to which it belongs
        neo_df = to_pandas_data_frame(graph.run(f"MATCH (n:{ann_entities[i]}) RETURN n.{imp_attributes[j]}, n.key "))  
        # We then iterate over the rows of the main df and the rows of the neo df
        for k,l in ((a,b) for a in range(len(main_df)) for b in range(len(neo_df))):
            # If the value of the important attribute in the neo df is type string, than it exists and we continue
            if type(neo_df.iloc[l,0])== str:
               # The rows of main_df are the unique articles
                # If that row is found in the key of a row in neo_df than we can assume that the value of the key belongs to the row of the main_df (and thus to an article)
                if main_df.index[k] in neo_df.iloc[l,1]:
                    # If the value in the main_df is a float than it is empty and we can just fill it with the value from the neo_df
                    if type(main_df.iloc[k,j]) == float:
                        main_df.iloc[k, j] = neo_df.iloc[l, 0]
                    # Else we have to add the value to the existing value in the df
                    else:
                        main_df.iloc[k,j] = main_df.iloc[k,j] + neo_df.iloc[l, 0]

# Add column aim to data frame
neo_df1 = to_pandas_data_frame(graph.run("MATCH (n:Experiment) RETURN n.description"))
neo_list = []

for i in range(0,len(neo_df1['n.description'])):
    string = str(neo_df1.iloc[i,0])
    neo_list.append(string)
neo_list

main_df['aim']=neo_list

# Step 4. Clean the data form unwanted stuff
for i, j in ((a, b) for a in range(len(main_df)) for b in range(len(main_df.columns))):
    if type(main_df.iloc[i,j]) != float:
        data = re.findall('(.+?)\s--', main_df.iloc[i,j])
        main_df.iloc[i,j] = data[0]

        
for i, j in ((a,b) for a in range(len(main_df)) for b in range(len(main_df.columns))):
        # If the type of df at loc[i, j] is not a float than it contains a string and we will manipulate it
        if type(main_df.iloc[i, j]) != float:
            # The string is stripped of the patterns `` 
            main_df.iloc[i, j] = main_df.iloc[i, j].replace("``", '')

outcome = ['positive','neutral','negative']
recommendation = [0,0,0]

main_df['outcome'] = outcome
main_df['recommendation'] = recommendation

main_df = main_df.fillna(0)

main_df = main_df.rename(columns={'method':'study type', 'timing':'start of the study'})
# Code for the dashboard
# The first part of the code is concerned with the lay out of the dashboard
url = 'http://127.0.0.1:8050/mainpage'
webbrowser.open_new(url) # Automatically open the webpage

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

APP_STYLE = {
    "display": "flex",    
}

# Here the fonts, size and colour of the sidebar are selected
SIDEBAR_STYLE = {
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
    "max-width": "16rem",
}

# The styles for the main content
CONTENT_STYLE = {
    "background-color": "#fff",
    "width": "100%",
    }


############ SIDEBAR
# The html div element is a generic containter for flow content
sidebar = html.Div([
        html.H2("SciModeler Dashboard", className="display-8"),
        html.Hr(),
        html.P(
            "The tool for researchers", className="lead"
        ),
# Nav and Navlink is used to create the hyperlinks towards the different pages of the dashboard        
        dbc.Nav(
            [
                dbc.NavLink("Filters", href="/mainpage", active="exact"),
                dbc.NavLink("Upload Article", href="/upload", active="exact"),
                dbc.NavLink("Annotate Article", href="/annotate", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
# html.br is used to create a line break, html.label is used to create a caption for an item in a user interface
# dcc.Dropdown is used to create the dropdown menu's
# The drop down menu's are interdepended meaning that you can Only select a new menu when the previous menu is selected    
         html.Div([
            html.Br(),
            html.Label('Aim'),
            # Options has to become the options that are leftover after filtering
             dcc.Dropdown(options=main_df['aim'].unique(),
                         multi=True,
                         id='aim-filter',
                         optionHeight=200),
            
            html.Br(),
            html.Label('Duration'),
            # Options has to become the options that are leftover after filtering
            dcc.Dropdown(multi=True, 
                         id='duration-filter'),
            
            html.Br(),
            html.Label('Location'),
            # Options has to become the options that are leftover after filtering
            dcc.Dropdown(multi=True,
                         id='location-filter',
                         optionHeight=50), 
            
            html.Br(),
            html.Label('Start of the study'),
            # Options has to become the options that are leftover after filtering
            dcc.Dropdown(multi=True, 
                         id='timing-filter'),
            
            html.Br(),
            html.Label('Study type'),
            # Options has to become the options that are leftover after filtering
            dcc.Dropdown(multi=True, 
                         id='method-filter',
                         optionHeight=50),
            
            html.Br(),
            html.Label('Results'),
            # Options has to become the options that are leftover after filtering
            dcc.Dropdown(multi=True, 
                         id='results-filter',
                         optionHeight=200),
            
        ], 
        style={'padding': 10, 'flex': 1}),
 
# The ConfirmDialogProvider creates the button to exit the Dashboard
# Children contains a list of the html.br components (dropdown menus)    
        dcc.ConfirmDialogProvider(
            children=[html.Br(),
            html.Button('exit')],
            id='exit-provider',
            message='Are you sure you want to exit the dashboard? '
                    'The server will be stopped. '
                    'Then you can close the page.'

        ),
        html.Div(id='output-provider'),
    ],
    style=SIDEBAR_STYLE,
    )
content = html.Div(id="page-content", style=CONTENT_STYLE)

app.layout = html.Div([dcc.Location(id="url"), sidebar, content],
                      style=APP_STYLE
                     )

############### Body
# In this part of the code the main body is created
# Callback functions are automatically used when an input component's property changes, to update another property in the output

##### Here the Mainpage is created
# def marks the start of the function, in this case is the function to render the page content
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/mainpage":
        return  html.Div([
            html.Div(children=[
            dcc.Markdown('''
        ## This is the dashboard for SciModeler

        #### Welcome to use!
        '''),
            ], style={
                'backgroundColor': '#f8f9fa',
                'padding': "1rem 1rem 1rem",
            }
                    ),


# This section creates the lay out of the Pie chart feature            
        html.Div(id='crossfilter-indicator-scatter', style={
        }),
 
# This section creates the lay out of the selection box feature
         html.Div(id='selected-table',
            style={
                "padding": "2rem 4rem 2rem",
            }),
    
# This section creates the lay out of the Recomandation box feature
        html.Div(id='recommendation-table',
            style={
                "padding": "2rem 4rem 2rem",
            }),
            
             
# Style               
        ], style={
                 })
          
##### End MAINPAGE

##### Upload Page
    elif pathname == "/upload":
        return html.Div(children=[
                      
                html.Div(
                 dcc.Markdown('''
                 ## Upload Your Annotations Below in .csv or .xlsx format
                 '''),
                    style={
                        'backgroundColor': '#f8f9fa',
                        'padding': "1rem 1rem 1rem",
                    }),
            
                html.Div(
                 dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select Files')
                    ]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '15px',
                    },
                    # Allow multiple files to be uploaded
                    multiple=True)),
                    dcc.Markdown('Refresh the webpage after you have uploaded the file, so the data can be included into the dashboard.', style={'padding': '1rem'}),
                    html.Div(id='output-data-upload'),
        ],  
                        style={
                                }),

##### End Upload page

##### Annotation file page
    elif pathname == "/annotate":

        return html.Div(children=[
            html.Div(
              dcc.Markdown('''
            ## Go to SciModeler for annotation
            https://louar.github.io/SciModeler-study-annotator/
            '''),
            style={
            'backgroundColor': '#f8f9fa',
            'padding': "1rem 1rem 1rem",
                 }),
          html.Div(
                dbc.Button(
                "Download the Instruction of Annotation",
                href="https://docs.google.com/spreadsheets/d/1HEetemXFyC5XN1zF5jOhShZS9KRzeiBF/edit?usp=sharing&ouid=116161135364733385865&rtpof=true&sd=true",
                download="my_data.txt",
                external_link=True,
                color="success",
            ), style={
            'padding': "1rem 1rem 1rem",
                })
        ])
      
###### End annoation file page  

def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')
    global main_df
    df = {}    # Initialize the dataframe, don't delete, otherwise it will raise the warning by linter
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename: # delete csv code
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

        elif 'xls' in filename:
            # Assume that the user uploaded an Excel file
            df = pd.read_excel(io.BytesIO(decoded), sheet_name='Annotations')

        # Merge df into main_df
        main_df = main_df.append(df)

    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])


    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),

        dash_table.DataTable(
            df.to_dict('records'),
            [{'name': i, 'id': i} for i in df.columns]
        ),

        html.Hr(),  # Horizontal line

        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])

##### Filter selections

@app.callback(
    Output('aim-filter', 'options'),
    Input ('aim-filter', 'value'))
def filter_1_df(aimfilter):
    return list(main_df['aim'].unique())

# The if statement is necessary to distinguish between a list of values as input and a singular input, we do this for every dropdown menu    
@app.callback(
    Output('duration-filter', 'options'),
    Input('aim-filter', 'value'))
def filter_aim_df(aimfilter):
    if type(aimfilter) != str:
        filter_df = main_df[main_df['aim'].isin(aimfilter)]
    else:
        filter_df = main_df[main_df['aim'] == aimfilter]
    return list(filter_df['duration'])

@app.callback(
     Output('location-filter', 'options'),
     Input('duration-filter', 'value'))
def filter_dur_df(durationfilter):
    print(durationfilter)
    if type(durationfilter) != str:
        filter_df = main_df[main_df['duration'].isin(durationfilter)]
    else:
        filter_df = main_df[main_df['duration'] == durationfilter]
    return list(filter_df['location'])
    
@app.callback(
    Output('timing-filter', 'options'),
    Input('location-filter', 'value'))
def filter_loc_df(locationfilter):
    if type(locationfilter) != str:
        filter_df = main_df[main_df['location'].isin(locationfilter)]
    else:
        filter_df = main_df[main_df['location'] == locationfilter]
    return list(filter_df['start of the study'])

@app.callback(
    Output('method-filter', 'options'),
    Input('timing-filter', 'value'))
def filter_tim_df(timingfilter):
    if type(timingfilter) != str:
        filter_df = main_df[main_df['start of the study'].isin(timingfilter)]
    else:
        filter_df = main_df[main_df['start of the study'] == timingfilter]
    return list(filter_df['study type'])

@app.callback(
    Output('results-filter', 'options'),
    Input('method-filter', 'value'))
def filter_met_df(methodfilter):
    if type(methodfilter) != str:
        filter_df = main_df[main_df['study type'].isin(methodfilter)]
    else:
        filter_df = main_df[main_df['study type'] == methodfilter]
    return list(filter_df['result'])

##### Creating tables out of filters for visualisation

# Recommendation table
@app.callback(
    Output('recommendation-table', 'children'),
    Input('results-filter', 'value'))
def recommendation_table(resultsfilter):
    if type(resultsfilter) != str:
        filter_df = main_df[main_df['result'].isin(resultsfilter)]
    else:
        filter_df = main_df[main_df['result'] == resultsfilter]
    
    rectable = html.Div([
            dbc.Label('The table below shows the recommendations of the filtered articles, hover over the recommendation to see the corresponding article:'),
            dash_table.DataTable(
                data=filter_df.to_dict('records'),
                columns=[{'id': c, 'name': c} for c in ['recommendation']],
                
                # Tooltip is used for pop-ups when hovering over the table with your mouse
                tooltip_data=[{
                    'recommendation': 'Article title: {}'.format(str(row['title'])),'type': 'markdown',
                    } for row in filter_df.to_dict('records')],
                
                # filter action is for the searchbar
                filter_action='native',
                sort_action='native',
                editable=True,
                
                # To color the data table with three different colors for positive, neutral and negative outcomes
                style_data_conditional=[
                    {
                        'if': {
                            'filter_query': '{outcome} = positive',
                            'column_id': 'recommendation',
                        },
                        'backgroundColor': '#00CC96',
                        'color': 'white'
                    },
                {
                        'if': {
                            'filter_query': '{outcome} = neutral',
                            'column_id': 'recommendation',
                        },
                        'backgroundColor': '#FFA15A',
                        'color': 'white'
                    },
                {
                        'if': {
                            'filter_query': '{outcome} = negative',
                            'column_id': 'recommendation',
                        },
                        'backgroundColor': '#EF553B',
                        'color': 'white'
                    }],
                tooltip_delay=0,
                tooltip_duration=None,
                style_data={
                    'border':'1px solid white',
                    'backgroundColor': '#dfe0e1',
                    'color': 'black',
                    'whiteSpace': 'normal',
                    'heigt': 'auto',
                },
                style_header={
                    'border':'1px solid white',
                    'backgroundColor': '#f8f9fa',
                    'color': 'black',
                }),            
        ])
    return rectable

# Selected Article table
@app.callback(
    Output('selected-table', 'children'),
    Input('results-filter', 'value'))
def selected_table(resultsfilter):
    if type(resultsfilter) != str:
        filter_df = main_df[main_df['result'].isin(resultsfilter)]
    else:
        filter_df = main_df[main_df['result'] == resultsfilter]
    
    selectedtable = html.Div([
            dbc.Label('The table below shows all filtered articles, hover with your mouse over an article to see the results:'),
            dash_table.DataTable(
                data=filter_df.to_dict('records'),
                columns=[{'id': c, 'name': c} for c in ['title']],
                tooltip_data=[{
                    'title': 'The results are: {}'.format(str(row['result'])),'type': 'markdown',
                } for row in filter_df.to_dict('records')],
                filter_action='native',
                sort_action='native',
                editable=True,
                style_data_conditional=[
                    {
                        'if': {
                            'filter_query': '{outcome} = positive',
                            'column_id': 'title',
                        },
                        'backgroundColor': '#00CC96',
                        'color': 'white'
                    },
                {
                        'if': {
                            'filter_query': '{outcome} = neutral',
                            'column_id': 'title',
                        },
                        'backgroundColor': '#FFA15A',
                        'color': 'white'
                    },
                {
                        'if': {
                            'filter_query': '{outcome} = negative',
                            'column_id': 'title',
                        },
                        'backgroundColor': '#EF553B',
                        'color': 'white'
                    }],
                tooltip_delay=0,
                tooltip_duration=None,
                style_data={
                    'border':'1px solid white',
                    'backgroundColor': '#dfe0e1',
                    'color': 'black',
                    'whiteSpace': 'normal',
                    'heigt': 'auto',
                },
                style_header={
                    'border':'1px solid white',
                    'backgroundColor': '#f8f9fa',
                    'color': 'black',
                }),
        ])
    return selectedtable

##### Creating pie chart

@app.callback(
    Output('crossfilter-indicator-scatter', 'children'),
    Input('results-filter', 'value'))
def update_graph(resultsfilter):
    if type(resultsfilter) != str:
        filter_df = main_df[main_df['result'].isin(resultsfilter)]
    else:
        filter_df = main_df[main_df['result'] == resultsfilter]
    filter_df['counts'] = filter_df.groupby(['outcome'])['title'].transform('count')
    filter_df = filter_df[['outcome', 'counts']]
    filter_df = filter_df.drop_duplicates()
    fig = px.pie(filter_df, values = 'counts', color='outcome',  
                 color_discrete_map={'positive': '#00CC96', 'neutral': '#FFA15A', 'negative': '#EF553B'},
                title="The pie chart below shows the percentages of positive, neutral and negative outcomes of the filtered articles")
                         
    return dcc.Graph(figure=fig)

##### Button to stop the server of our dashboard

@app.callback(Output('output-provider', 'children'),
              Input('exit-provider', 'submit_n_clicks'))
def update_output(submit_n_clicks):
    if not submit_n_clicks:
        return ''
    else:
        os.kill(os.getpid(), signal.SIGTERM)

##### Shows a preview of the dataframe with the uploaded file

@app.callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children
    
    
if __name__ == "__main__":
    app.run_server()
    


# In[ ]:




