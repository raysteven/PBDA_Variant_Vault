import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
from dash import callback_context
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import dash_loading_spinners


import base64
import os
import shutil  # For file copying
import time
import threading


from PBTK import *
import pandas as pd
from sqlalchemy import create_engine
import sqlite3
from sqlalchemy import text

pgnum = 0

# Home page layout
layout = html.Div(
     children=[
             html.Div(
                 id=f"div-loading-{pgnum}",
                 children=[
                     dash_loading_spinners.Pacman(
                         fullscreen=True, 
                         id="loading-whole-app"
                     )
                 ]
             ),
             html.Div(
                 className="div-app",
                 id=f"div-app-{pgnum}",
                 children = [ #  app layout here

                    html.Div([
                        html.H5('Home Page'),
                        html.Div([
                        html.P('Welcome to the home page of this PBDA!'),
                        html.P('You can use the available tools from the navigation bar on the top right of the page.')
                        ], style={'margin':'0'})
                    ], style={'margin':'20px', 'fontFamily':'Monaco, monospace'})

                ]
             )
         ]
     )

def register_callbacks(app):
    @app.callback(
            Output(f"div-loading-{pgnum}", "children"),
            [
                Input(f"div-app-{pgnum}", "loading_state")
            ],
            [
                State(f"div-loading-{pgnum}", "children"),
            ]
        )
    def hide_loading_after_startup(
            loading_state, 
            children
            ):
            if children:
                print("remove loading spinner!")
                return None
            print("spinner already gone!")
            raise PreventUpdate




# Since the homepage might not need callbacks, we don't include them here.
# However, you could define callbacks similarly to the other pages if needed.
