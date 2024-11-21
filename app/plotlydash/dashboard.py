import dash
import plotly.express as px
from flask import Flask
from app.plotlydash.data import fetch_data
import numpy as np
import pandas as pd


def init_dash_app(server):
    # Initialize Dash app with the parent Flask app 
    # With this setup Dash piggybacks off of the Flask server as a module, opposed to running as a standalone server
    server.logger.info("Initializing Dash app.")
    dash_app = dash.Dash(
        server=server,
        routes_pathname_prefix='/dash/',
        external_stylesheets=[
            '/static/dist/css/styles.css',
        ]
    )

    dash_app.layout = dash.html.Div(id='dash-container', children=[
        dash.dcc.Location(id="url", refresh=False),
        dash.dcc.Store(id="data-store"),  # Store to hold fetched data
        dash.dcc.Graph(id='budget-graph') 
    ])
    
    init_callbacks(dash_app)

    return dash_app.server
    
def init_callbacks(dash_app):
    @dash_app.callback(
    dash.Output("data-store", "data"),
    dash.Input("url", "pathname")
    )
    def load_data(pathname):
        try:
            trip_id = int(pathname.split("/")[-1])  # Attempt to extract trip ID
        except (ValueError, IndexError):
            return None
        
        data = fetch_data(trip_id)
        return data
    
    @dash_app.callback(
        dash.Output("budget-graph", "figure"),
        dash.Input("data-store", "data")
    )
    def update_graph(data):
        if data:
            # Convert data into a pandas DataFrame
            df = pd.DataFrame(data)

            # Check if required columns exist
            required_columns = ["base_cost", "component_name", "exchange_rate", "category_name", "title"]
            if not all(col in df.columns for col in required_columns[:-1]):  # Exclude "title" as it's not a column
                raise ValueError(f"Missing one or more required columns: {required_columns[:-1]}")

            # Filter rows where base_cost > 0
            df = df[df["base_cost"] > 0]

            if df.empty:
                return px.line(title="No valid data to display.")

            # Calculate adjusted cost
            df["adjusted_cost"] = df["base_cost"] * df["exchange_rate"]

            # Create a bar plot
            fig = px.bar(
                data_frame=df,
                x="component_name",
                y="adjusted_cost",
                title=data["title"],
                labels={"component_name": "Component", "adjusted_cost": "Cost"},
                color="category_name"
            )
            return fig
        # Placeholder figure if no data is loaded yet
        return px.line(title="Waiting for data...")
    