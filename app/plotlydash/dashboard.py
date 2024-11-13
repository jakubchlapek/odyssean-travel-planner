import dash
import plotly.express as px
from flask import Flask

def init_dash_app(server):
    # Initialize Dash app with the parent Flask app 
    # With this setup Dash piggybacks off of the Flask server as a module, opposed to running as a standalone server
    dash_app = dash.Dash(
        server=server,
        routes_pathname_prefix='/dash/',
        external_stylesheets=[
            '/static/dist/css/styles.css',
        ]
    )

    dash_app.layout = dash.html.Div(id='dash-container', children=[
        dash.dcc.Graph(
            id='example-graph',
            figure=px.line(x=[1, 2, 3, 4], y=[10, 11, 12, 13], title="Simple Line Plot")
        )])

    # init_callbacks(dash_app)

    return dash_app.server


# def init_callbacks(dash_app):
#     @dash_app.callback(
#     # Callback input/output
#     ...
#     )
#     def update_graph(rows):
#         # Callback logic
#         ...