from dash import Dash, html, dcc, Input, Output
import plotly.express as px
from flask import Flask
from app.plotlydash.data import fetch_data, get_trip_info
import numpy as np
import pandas as pd

def init_dash_app(server):
    # Initialize Dash app with the parent Flask app 
    # With this setup Dash piggybacks off of the Flask server as a module, opposed to running as a standalone server
    server.logger.info("Initializing Dash app.")
    dash_app = Dash(
        server=server,
        routes_pathname_prefix='/dash/',
        external_stylesheets=[
            '/static/css/graphs.css',
        ]
    )
    
    dash_app.layout = html.Div(id='dash-container', children=[
        dcc.Location(id="url", refresh=False),
        dcc.Store(id="data-store"),  # Store to hold fetched data
        html.H1(id="trip-title", children=[]),
        html.Div(id='budget-graphs-box', children=[
            dcc.Graph(id='budget-bar-graph'), 
            dcc.Graph(id='budget-pie-graph')
        ]),
        html.Div(id="graph-buttons", children=[
            html.Label('Choose categories'),
            dcc.Dropdown(
                options=[
                    {'label': 'Accommodation', 'value': 'Accommodation'},
                    {'label': 'Food', 'value': 'Food'},
                    {'label': 'Transport', 'value': 'Transport'},
                    {'label': 'Entertainment', 'value': 'Entertainment'},
                    {'label': 'Other', 'value': 'Other'}
                ],                
                value=['Accommodation', 'Food', 'Transport', 'Entertainment', 'Other'],
                id="dropdown-categories",
                multi=True,
            )
        ])

    ])
    
    init_callbacks(dash_app)

    return dash_app.server
    
def init_callbacks(dash_app):    
    @dash_app.callback(
    Output("data-store", "data"),
    Input("url", "pathname")
    )
    def load_data(pathname):
        try:
            trip_id = int(pathname.split("/")[-1])  # Attempt to extract trip ID
        except (ValueError, IndexError):
            return None
        
        data = fetch_data(trip_id)
        return data
    
    @dash_app.callback(
        Output("trip-title", "children"),
        Input("url", "pathname")
    )
    def get_title(pathname):
        try:
            trip_id = int(pathname.split("/")[-1])  # Attempt to extract trip ID
        except (ValueError, IndexError):
            return None
        
        trip_name, trip_cost, preferred_currency = get_trip_info(trip_id)
        return f"Trip: {trip_name} - total cost: {trip_cost} {preferred_currency}"
    
    @dash_app.callback(
        Output("budget-bar-graph", "figure"),
        Input("data-store", "data"),
        Input("dropdown-categories", "value")
    )
    def add_bar_graph(data, chosen_categories):
        if data:
            df = pd.DataFrame(data[0])
            preferred_currency = data[1]

            required_columns = ["base_cost", "component_name", "exchange_rate", "category_name"]
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"Missing one or more required columns: {required_columns}")

            # Filter rows where base_cost > 0
            df = df[df["base_cost"] > 0]
            
            # Filter by chosen_categories
            df = df[df["category_name"].isin(chosen_categories)]

            if df.empty:
                return px.line(title="No valid data to display.")

            df["adjusted_cost"] = df["base_cost"] * df["exchange_rate"]

            fig = px.bar(
                data_frame=df,
                x="component_name",
                y="adjusted_cost",
                title= f"",
                labels={"component_name": "Component", "adjusted_cost": "Cost"},
                color="category_name",  
                color_discrete_map={
                    'Accommodation': '#EA4848', 
                    'Food': '#4FB477', 
                    'Transport': '#85CCFF',
                    'Entertainment': '#A975A4',
                    'Shopping': '#FF9B42',
                    'Other': '#B8B8B8'
                },
                hover_data={"start_date": True, "end_date": True, "link": True, "category_name": False},
                hover_name="description",
                custom_data=["start_date", "end_date", "link"],
                width=365,
                height=365
            )
            fig.update_layout(
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=12,
                    font_family="Fira Sans",
                ),
                paper_bgcolor="#f3ebdf",
                plot_bgcolor="#f3ebdf",
                barmode="relative",
                xaxis_title="Component",
                yaxis_title=f"Cost ({preferred_currency})",
                showlegend=True,
                legend_title="Category",       
                margin=dict(l=30, r=0, t=40, b=30),
                font_family="Fira Sans",     
            )
            fig.update_traces(
                hovertemplate="<b>%{x}</b><br><br>" +
                              "Cost: %{y:.2f}" + f"{preferred_currency}<br>" +
                              "Description: %{hovertext}<br>" +
                              "Start date: %{customdata[0]}<br>" +
                              "End date: %{customdata[1]}<br>" +
                              "Link: %{customdata[2]}<extra></extra>",
                marker=dict(line=dict(width=1, color="Black")),
                               
            )
            return fig
        # Placeholder figure if no data is loaded yet
        return px.line(title="Waiting for data...", height=365, width=365)    
    
    @dash_app.callback(
        Output("budget-pie-graph", "figure"),
        Input("data-store", "data"),
        Input("dropdown-categories", "value")
    )
    def add_pie_graph(data, chosen_categories):
        if data:
            df = pd.DataFrame(data[0])
            preferred_currency = data[1]

            required_columns = ["base_cost", "component_name", "exchange_rate", "category_name"]
            if not all(col in df.columns for col in required_columns):  # Exclude "title" and "preferred_currency" as it's not a column
                raise ValueError(f"Missing one or more required columns: {required_columns}")
            
            # Filter by chosen_categories
            df = df[df["category_name"].isin(chosen_categories)]
            
            fig = px.pie(
                data_frame=df,
                values="base_cost",
                names="component_name",
                color="category_name",  
                color_discrete_map={
                    'Accommodation': '#EA4848', 
                    'Food': '#4FB477', 
                    'Transport': '#85CCFF',
                    'Entertainment': '#A975A4',
                    'Shopping': '#FF9B42',
                    'Other': '#B8B8B8'
                },
                width=365,
                height=365,
                custom_data=["category_name", "type_name"],
            )
            fig.update_layout(
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=12,
                    font_family="Fira Sans",
                ),
                margin=dict(l=0, r=30, t=40, b=30),
                paper_bgcolor="#f3ebdf",
                plot_bgcolor="#f3ebdf",
                legend_title="Component name",
                font_family="Fira Sans",     
            )
            fig.update_traces(
                textposition="inside",
                textinfo='percent+label',
                hovertemplate="<b>%{name}</b><br><br>" +
                    "Cost: %{value:.2f}" + f"{preferred_currency}<br>" +
                    "Category: %{customdata[0]}<br>" +
                    "Subcategory: %{customdata[1]}<extra><extra>",
            )
            return fig
        # Placeholder figure if no data is loaded yet
        return px.line(title="Waiting for data...", height=365, width=365)