from dash import Dash, html, dcc, Input, Output
import plotly.express as px
from flask import Flask
from app.plotlydash.data import fetch_trip_data, fetch_participants
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
        dcc.Store(id="data-store-trip"),  # Store to hold fetched data
        dcc.Store(id="data-store-participants"),  # Store to hold fetched participants
        html.H1(id="trip-title", children=[]),
        html.Div(id='budget-graphs-box', children=[
            dcc.Graph(id='budget-bar-graph'), 
            dcc.Graph(id='budget-pie-graph')
        ]),
        html.Div(id="graph-buttons", children=[
            html.Div(id="categories-box", children=[
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
                    ),
            ]),
            html.Div(id="participants-box", children=[
                html.Label('Choose participants'),
                dcc.Dropdown(
                    options=[],
                    id="dropdown-participants",
                    multi=True,
                    ),
            ]),
            dcc.RadioItems(
                options=[
                    {'label': 'Include free components', 'value': True},
                    {'label': 'Exclude free components', 'value': False}
                ],
                value=True,
                id="radio-include-free"
            )
        ])

    ])
    
    init_callbacks(dash_app)

    return dash_app.server
    
    
def filter_df(trip_data: dict, chosen_categories: list[str], chosen_participants: list[str], include_free: bool) -> pd.DataFrame:
    """Filters the data provided based on the settings chosen by user and returns a panda dataframe"""
    df = pd.DataFrame(trip_data)
    required_columns = ["base_cost", "component_name", "exchange_rate", "category_name"]
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"Missing one or more required columns: {required_columns}")
    
    # Filter by chosen participants
    temp_df = pd.DataFrame()
    if chosen_participants:
        if -1 in chosen_participants:
            temp_df = df[df["participant_id"].isna()]
        df = df[df["participant_id"].isin(chosen_participants)]
    df = pd.concat([df, temp_df])
    # Filter rows where base_cost > 0
    if not include_free:
        df = df[df["base_cost"] > 0]
        
    # Filter by chosen_categories
    if chosen_categories:
        df = df[df["category_name"].isin(chosen_categories)] 
    
    return df
    

def init_callbacks(dash_app):    
    @dash_app.callback(
    Output("data-store-trip", "data"),
    Input("url", "pathname")
    )
    def load_data(pathname):
        try:
            trip_id = int(pathname.split("/")[-1])  # Attempt to extract trip ID
        except (ValueError, IndexError):
            return None
        
        data = fetch_trip_data(trip_id)
        return data
    
    @dash_app.callback(
    Output("data-store-participants", "data"),
    Input("url", "pathname")
    )
    def load_participants(pathname):
        try:
            trip_id = int(pathname.split("/")[-1])  # Attempt to extract trip ID
        except (ValueError, IndexError):
            return None
        
        participants = fetch_participants(trip_id)
        return participants
    
    @dash_app.callback(
    Output("dropdown-participants", "options"), 
    Output("dropdown-participants", "value"),
    Input("data-store-participants", "data"),
    )
    def update_dropdown_from_store(participants):
        dropdown_options = [{"label": p[0], "value": p[1]} for p in participants]
        dropdown_options.append({"label": "Shared components", "value": -1})
        return dropdown_options, participants
    
    @dash_app.callback(
        Output("trip-title", "children"),
        Input("data-store-trip", "data"),
        Input("dropdown-categories", "value"),
        Input("dropdown-participants", "value"),
        Input("radio-include-free", "value")
    )
    def get_title(data, chosen_categories, chosen_participants, include_free):
        if not data:
            return "No data loaded yet."
        df = filter_df(data[0], chosen_categories, chosen_participants, include_free)
        trip_cost = np.sum(df["base_cost"] * df["exchange_rate"])
        preferred_currency = data[1]
        trip_name = data[2]
        return f"Trip: {trip_name} - total cost: {trip_cost:.2f} {preferred_currency}"
    
    @dash_app.callback(
        Output("budget-bar-graph", "figure"),
        Input("data-store-trip", "data"),
        Input("dropdown-categories", "value"),
        Input("dropdown-participants", "value"),
        Input("radio-include-free", "value")
    )
    def add_bar_graph(data, chosen_categories, chosen_participants, include_free):
        if not data:
            # Placeholder figure if no data is loaded yet
            return px.line(title="Waiting for data...", height=365, width=365)    
            
        df = filter_df(data[0], chosen_categories, chosen_participants, include_free)
        preferred_currency = data[1]

        if df.empty:
            return px.line(title="No valid data to display.", height=365, width=365)

        df["adjusted_cost"] = df["base_cost"] * df["exchange_rate"]

        fig = px.bar(
            data_frame=df,
            x="component_name",
            y="adjusted_cost",
            title= f"Cost breakdown by component",
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
        fig.update_xaxes(
            tickangle=45,
            tickfont=dict(size=10),
            categoryorder="total ascending",
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
    
    @dash_app.callback(
        Output("budget-pie-graph", "figure"),
        Input("data-store-trip", "data"),
        Input("dropdown-categories", "value"),
        Input("dropdown-participants", "value"),
        Input("radio-include-free", "value")
    )
    def add_pie_graph(data, chosen_categories, chosen_participants, include_free):
        if not data:
            # Placeholder figure if no data is loaded yet
            return px.line(title="Waiting for data...", height=365, width=365)    
        df = filter_df(data[0], chosen_categories, chosen_participants, include_free)
        preferred_currency = data[1]

        if df.empty:
            return px.line(title="No valid data to display.", height=365, width=365)
        
        fig = px.pie(
            data_frame=df,
            values="base_cost",
            names="category_name",
            title="Cost breakdown by category",
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
            hovertemplate="<b>%{names}</b><br><br>" +
                "Cost: %{value:.2f}" + f"{preferred_currency}<br>" +
                "Category: %{customdata[0]}<br>" +
                "Subcategory: %{customdata[1]}<extra></extra>",
            marker=dict(line=dict(width=1, color="Black")),
        )
        return fig
