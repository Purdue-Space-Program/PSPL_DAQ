import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import re
import os
import argparse
from collections import defaultdict
from . import datareducer as dr

THEME = "plotly_dark" # Options: 'plotly_white' (default, with grid), 'plotly_dark'
# 3. PLOT DOWNSAMPLING
# For performance, downsample data if it exceeds this number of points.
# This speeds up plotting for large time ranges. Zooming in will still show high-res data.
# Set to None to disable. A value around 50,000 is good for interactivity.
MAX_PLOT_POINTS = 50000
# 4. SENSORS TO PLOT
# Define each sensor you want to plot. You can add as many as you need.
# - 'column': The exact column name from your Parquet file.
# - 'name': A user-friendly name for the plot legend.
# - 'color': The line color (e.g., 'blue', '#FF5733').
# - 'yaxis': Which y-axis to use. 'y1' for left, 'y2' for right.
# 5. TIME RANGE
# Format: 'YYYY-MM-DD HH:MM:SS'. Set to None to use the full time range.
def create_interactive_plot(range_name, input_list):
    INPUT_FILE = rf"daq_system/utils/{range_name}/reduced_{range_name}.parquet"
    PLOT_TITLE  = input_list[0]
    X_AXIS_LABEL = input_list[1]
    Y1_AXIS_LABEL = input_list[2]
    Y2_AXIS_LABEL = input_list[3]
    OUTPUT_FILENAME = input_list[4]
    START_TIME = input_list[5]
    END_TIME = input_list[6]
    SENSORS_TO_PLOT = input_list[7]
    """
    Loads resampled data and creates a high-quality, interactive HTML plot
    with support for dual y-axes and advanced styling.
    """
    pio.templates.default = THEME
    print(f"Reading data from '{INPUT_FILE}'...")
    try:
        df = pd.read_parquet(INPUT_FILE)
    except Exception as e:
        print(
            f"Error: Could not read '{INPUT_FILE}'. Please ensure you have run the data_resampling.py script first."
        )
        print(f"Details: {e}")
        return
    time_col = "timestamp"
    if time_col not in df.columns:
        print(
            f"Error: The required '{time_col}' column was not found in the Parquet file."
        )
        return
    df[time_col] = pd.to_datetime(df[time_col])
    df.set_index(time_col, inplace=True)
    df.sort_index(inplace=True)
    df_filtered = df.loc[START_TIME:END_TIME]
    if df_filtered.empty:
        print("Error: No data found in the specified time range.")
        return
    # --- Downsample for Performance ---
    if MAX_PLOT_POINTS and len(df_filtered) > MAX_PLOT_POINTS:
        print(
            f"Data has {len(df_filtered)} points, exceeding the limit of {MAX_PLOT_POINTS}. Downsampling for performance..."
        )
        # Calculate the appropriate resampling rule to get close to MAX_PLOT_POINTS
        duration_seconds = (
            df_filtered.index[-1] - df_filtered.index[0]
        ).total_seconds()
        if duration_seconds > 0:
            interval_ms = (duration_seconds / MAX_PLOT_POINTS) * 1000
            resample_rule = (
                f"{max(1, int(interval_ms))}ms"  # Ensure at least 1ms interval
            )
            df_plot = df_filtered.resample(resample_rule).mean()
            print(
                f"Downsampled to {len(df_plot)} points using a '{resample_rule}' interval."
            )
        else:
            df_plot = df_filtered  # Cannot resample if no duration
    else:
        df_plot = df_filtered
    if df_plot.empty:
        print("Error: No data to plot after filtering and downsampling.")
        return
    print(f"Plotting {len(df_plot)} data points...")
    # --- Create the Interactive Plot with a secondary Y-axis ---
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    for sensor in SENSORS_TO_PLOT:
        if sensor["column"] in df_plot.columns:
            fig.add_trace(
                go.Scatter(
                    x=df_plot.index,
                    y=df_plot[sensor["column"]],
                    mode="lines",
                    name=sensor["name"],
                    line=dict(color=sensor["color"]),
                ),
                secondary_y=(sensor["yaxis"] == "y2"),
            )
        else:
            print(
                f"Warning: Column '{sensor['column']}' not found and will be skipped."
            )
    # --- Formatting for Professional Appearance ---
    fig.update_layout(
        title=dict(text=PLOT_TITLE, font=dict(size=20), x=0.5),
        xaxis_title=X_AXIS_LABEL,
        legend_title_text="Sensors",
    )
    # Set y-axes titles
    fig.update_yaxes(title_text=Y1_AXIS_LABEL, secondary_y=False)
    fig.update_yaxes(title_text=Y2_AXIS_LABEL, secondary_y=True)
    try:
        fig.write_html(rf"daq_system/utils/{range_name}/{range_name}_{OUTPUT_FILENAME}.html")
        print(f"Successfully saved interactive plot to '{OUTPUT_FILENAME}'")
    except Exception as e:
        print(f"Error: Could not save the plot file. Details: {e}")