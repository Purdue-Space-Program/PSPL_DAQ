import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import re
import os
import argparse
from collections import defaultdict
from daq_system.config.settings import DAQConfig, DEFAULT_DEVICE_PATHS
from colorama import Fore, Style
import synnax as sy
import colorama
import yaml
import csv
from . import datareducer as dr
from . import dataprocessor as dp
from . import export as ex

def export_reduce_process(raw_data_file, range_name):
    input_lists = [
        [
            "RTDs", #plot title
            "Time", #x axis title
            "Voltage (V)",  # Label for the LEFT y-axis
            " ", # Label for the RIGHT y-axis
            "RTDs",  # Interactive HTML file
            None,  # start time Example: '2025-09-19 14:30:00'
            None,  # end time
            [
                {
                "column": "RTD-FU",
                "name": "RTD-FU",
                "color": "#D62728",  # Red
                "yaxis": "y1",
                },
                {
                "column": "RTD-OX",
                "name": "RTD-OX",
                "color": "#1B3CDF",  # Blue
                "yaxis": "y1",
                },
            ],
        ],
        [
            "Vehicle Pressures", #plot title
            "Time", #x axis title
            "Pressure(PSI)",  # Label for the LEFT y-axis
            "Pressure(PSI)", # Label for the RIGHT y-axis
            "Vehicle Pressures",  # Interactive HTML file
            None,  # start time Example: '2025-09-19 14:30:00'
            None,  # end time
            [
                {
                "column": "PT-HE-201",
                "name": "PT-HE-201",
                "color": "#27D684",  # helium
                "yaxis": "y1",
                },
                {
                "column": "PT-HE-01",
                "name": "PT-HE-01",
                "color": "#27D684",  # helium
                "yaxis": "y1",
                },
                {
                "column": "PT-FU-201",
                "name": "PT-FU-201",
                "color": "#D62728",  # Red
                "yaxis": "y2",
                },
                {
                "column": "PT-OX-201",
                "name": "PT-OX-201",
                "color": "#1B3CDF",  # Blue
                "yaxis": "y2",
                },
            ],
        ],
        [
                "Vehicle Temperatures", #plot title
                "Time", #x axis title
                "Temperature(K)",  # Label for the LEFT y-axis
                "", # Label for the RIGHT y-axis
                "Vehicle Temperatures",  # Interactive HTML file
                None,  # start time Example: '2025-09-19 14:30:00'
                None,  # end time
                [
                    {
                    "column": "TC-HE-201",
                    "name": "TC-HE-201",
                    "color": "#27D684",  # helium
                    "yaxis": "y1",
                    },
                    {
                    "column": "TC-FU-201",
                    "name": "TC-FU-201",
                    "color": "#D62728",  # Red
                    "yaxis": "y1",
                    },
                    {
                    "column": "TC-OX-201",
                    "name": "TC-OX-201",
                    "color": "#1B3CDF",  # Blue
                    "yaxis": "y1",
                    },
                ],
            ],
        [
            "Hotfire Pressures", #plot title
            "Time", #x axis title
            "Pressure(PSI)",  # Label for the LEFT y-axis
            "Thrust(LBF)", # Label for the RIGHT y-axis
            "Hotfire Pressures",  # Interactive HTML file
            None,  # start time Example: '2025-09-19 14:30:00'
            None,  # end time
            [
                {
                "column": "PT-FU-202",
                "name": "PT-FU-202",
                "color": "#D62728",  # Red
                "yaxis": "y1",
                },
                {
                "column": "PT-OX-202",
                "name": "PT-OX-202",
                "color": "#1B3CDF",  # Blue
                "yaxis": "y1",
                },
                {
                "column": "PT-CHAMBER",
                "name": "PT-CHAMBER",
                "color": "#D69F27",  # Orange
                "yaxis": "y1",
                },
                {
                "column": "FMS",
                "name": "FMS",
                "color": "#B81BDF",  # Purple
                "yaxis": "y2",
                },
            ],
        ],
        [
            "Fill Pressures", #plot title
            "Time", #x axis title
            "Pressure (PSI)",  # Label for the LEFT y-axis
            "", # Label for the RIGHT y-axis
            "Fill Pressures",  # Interactive HTML file
            None,  # start time Example: '2025-09-19 14:30:00'
            None,  # end time
            [
                {
                "column": "PT-FU-04",
                "name": "PT-FU-04",
                "color": "#D62728",  # Red
                "yaxis": "y1",
                },
                {
                "column": "PT-OX-04",
                "name": "PT-OX-04",
                "color": "#1B3CDF",  # Blue
                "yaxis": "y1",
                },
                
            ],
        ],
        [
            "Fill Temperatures", #plot title
            "Time", #x axis title
            "Temperatures(K)",  # Label for the LEFT y-axis
            "", # Label for the RIGHT y-axis
            "Fill Temperatures",  # Interactive HTML file
            None,  # start time Example: '2025-09-19 14:30:00'
            None,  # end time
            [
                {
                "column": "TC-FU-04",
                "name": "TC-FU-04",
                "color": "#D62728",  # Red
                "yaxis": "y1",
                },
                {
                "column": "TC-OX-04",
                "name": "TC-OX-04",
                "color": "#1B3CDF",  # Blue
                "yaxis": "y1",
                },
                
            ],
        ],
        [
            "Fill Temperatures", #plot title
            "Time", #x axis title
            "Temperatures(K)",  # Label for the LEFT y-axis
            "", # Label for the RIGHT y-axis
            "Fill Temperatures",  # Interactive HTML file
            None,  # start time Example: '2025-09-19 14:30:00'
            None,  # end time
            [
                {
                "column": "TC-FU-04",
                "name": "TC-FU-04",
                "color": "#D62728",  # Red
                "yaxis": "y1",
                },
                {
                "column": "TC-OX-04",
                "name": "TC-OX-04",
                "color": "#1B3CDF",  # Blue
                "yaxis": "y1",
                },
                
            ],
        ],
    ]
    ex.export_data(range_name)
    dr.process_data_reduction(raw_data_file, range_name)
    for input_list in input_lists:
        dp.create_interactive_plot(range_name, input_list)

if __name__ == "__main__":
    range_name = "10-29-LoxFill"
    raw_data_file = rf"daq_system/utils//{range_name}/datadump_{range_name}.csv"
    export_reduce_process(raw_data_file, range_name)
    