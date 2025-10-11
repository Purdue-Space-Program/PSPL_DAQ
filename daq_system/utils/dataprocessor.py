import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
# --- Advanced Configuration ---
# Customize your entire plot from this section.
# 1. INPUT FILE
INPUT_FILE = "reduced_data.parquet"
# 2. PLOT THEME
# Switch between a professional light or dark theme.
# Options: 'plotly_white' (default, with grid), 'plotly_dark'
THEME = "plotly_white"
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
SENSORS_TO_PLOT = [
    {
        "column": "PT-HE-201",
        "name": "PT-HE-201",
        "color": "#1F77B4",  # Muted Blue
        "yaxis": "y1",
    },
    {
        "column": "PT-FU-201",
        "name": "PT-FU-201",
        "color": "#FF7F0E",  # Safety Orange
        "yaxis": "y2",
    },
    {
        "column": "PT-OX-201",
        "name": "PT-OX-201",
        "color": "#D62728",  # Barn Red
        "yaxis": "y2",
    },
]
# 5. TIME RANGE
# Format: 'YYYY-MM-DD HH:MM:SS'. Set to None to use the full time range.
START_TIME = None  # Example: '2025-09-19 14:30:00'
END_TIME = None  # Example: '2025-09-19 14:45:00'
# 6. PLOT APPEARANCE
PLOT_TITLE = "Flow"
X_AXIS_LABEL = "Time"
Y1_AXIS_LABEL = "Pressure (PSI)"  # Label for the LEFT y-axis
Y2_AXIS_LABEL = "Temperature (°F)"  # Label for the RIGHT y-axis
OUTPUT_FILENAME = "onboard_sensors.html"  # Interactive HTML file
def create_interactive_plot():
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
        fig.write_html(OUTPUT_FILENAME)
        print(f"Successfully saved interactive plot to '{OUTPUT_FILENAME}'")
    except Exception as e:
        print(f"Error: Could not save the plot file. Details: {e}")
if __name__ == "__main__":
    create_interactive_plot()





8:06
import pandas as pd
import re
import os
import argparse
from collections import defaultdict
# --- Required Libraries ---
# Before running, ensure you have the necessary libraries installed in your environment:
# uv pip install pandas pyarrow fastparquet
# --- Configuration ---
# The paths where the reduced data will be saved.
OUTPUT_PARQUET_FILEPATH = "reduced_data.parquet"
OUTPUT_CSV_FILEPATH = "reduced_data.csv"  # New CSV output path
# The resampling frequency. '1s' (1 second), '100ms' (100 milliseconds), '10ms' (10 milliseconds).
# A smaller value retains more detail but results in a larger file.
RESAMPLE_FREQ = "10ms"
# The number of rows to process at a time. Adjust based on your system's RAM.
CHUNKSIZE = 1_000_000
def find_column_groups(columns):
    """
    Analyzes column names to group data columns with their associated time columns.
    """
    time_col_map = defaultdict(list)
    data_cols_with_time = set()
    time_cols = [c for c in columns if "time" in c.lower()]
    for t_col in time_cols:
        base_name = re.sub(r"(_time|_TIME)", "", t_col)
        # BCLS_di_time_PI-HE-01 -> PI-HE-01
        base_name_short = base_name.split("_")[-1]
        # Find exact matches or derived matches
        for d_col in columns:
            if d_col == base_name or d_col == base_name_short:
                if d_col not in data_cols_with_time:
                    time_col_map[t_col].append(d_col)
                    data_cols_with_time.add(d_col)
    # Handle the special 'BCLS_ai_time' case which covers multiple columns
    if "BCLS_ai_time" in time_cols:
        ai_cols = [
            "PT-FU-04",
            "PT-HE-01",
            "PT-OX-04",
            "PT-N2-01",
            "PT-FU-02",
            "PT-OX-02",
            "TC-OX-04",
            "TC-FU-04",
            "TC-OX-02",
            "TC-FU-02",
            "RTD-OX",
            "RTD-FU",
            "TC-HE-201",
        ]
        for col in ai_cols:
            if col in columns and col not in data_cols_with_time:
                time_col_map["BCLS_ai_time"].append(col)
                data_cols_with_time.add(col)
    # Identify any columns that weren't grouped
    unmapped_cols = set(columns) - data_cols_with_time - set(time_cols)
    if unmapped_cols:
        print(
            f"Warning: The following columns could not be mapped to a time column and will be ignored: {unmapped_cols}"
        )
    return time_col_map
def process_data_reduction(input_filepath):
    """
    Processes a large CSV file in chunks, applies time corrections, resamples
    the data to a consistent frequency, and saves the result to Parquet and CSV files.
    """
    print(f"Reading header from '{input_filepath}' to determine column structure...")
    try:
        header_df = pd.read_csv(input_filepath, nrows=0)
        column_groups = find_column_groups(header_df.columns)
    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_filepath}'")
        return
    print("Identified the following data groups:")
    for time_col, data_cols in column_groups.items():
        print(f" - Time Column: '{time_col}' -> Data Columns: {len(data_cols)}")
    # --- Time Correction Configuration ---
    time_offset = pd.Timedelta(seconds=10.614)
    time_cols_to_shift = {"PT-HE-201_time", "PT-FU-201_time", "PT-OX-201_time"}
    shifted_cols_reported = (
        set()
    )  # Used to print the correction message only once per column
    all_resampled_chunks = []
    print(f"\nStarting to process file in chunks of {CHUNKSIZE:,} rows...")
    chunk_num = 1
    with pd.read_csv(input_filepath, chunksize=CHUNKSIZE, low_memory=False) as reader:
        for chunk in reader:
            print(f"  Processing chunk {chunk_num}...")
            chunk_num += 1
            resampled_groups_in_chunk = []
            for time_col, data_cols in column_groups.items():
                cols_to_load = [time_col] + data_cols
                group_df = chunk[cols_to_load].copy()
                group_df.dropna(subset=[time_col], inplace=True)
                if group_df.empty:
                    continue
                group_df[time_col] = pd.to_datetime(group_df[time_col], errors="coerce")
                # --- Apply Time Correction for specific sensors ---
                if time_col in time_cols_to_shift:
                    if time_col not in shifted_cols_reported:
                        print(
                            f"Applying -{time_offset.total_seconds()}s time correction to '{time_col}'."
                        )
                        shifted_cols_reported.add(time_col)
                    group_df[time_col] = group_df[time_col] - time_offset
                group_df.dropna(subset=[time_col], inplace=True)
                group_df.set_index(time_col, inplace=True)
                # Ensure data columns are numeric, coercing errors
                for col in data_cols:
                    group_df[col] = pd.to_numeric(group_df[col], errors="coerce")
                if not group_df.empty:
                    resampled = group_df.resample(RESAMPLE_FREQ).mean()
                    resampled_groups_in_chunk.append(resampled)
            if resampled_groups_in_chunk:
                combined_chunk = pd.concat(resampled_groups_in_chunk, axis=1)
                all_resampled_chunks.append(combined_chunk)
    if not all_resampled_chunks:
        print(
            "No data was processed. The input file might be empty or in an unexpected format."
        )
        return
    print("\nAll chunks processed. Combining results...")
    final_df = pd.concat(all_resampled_chunks)
    final_df = final_df.groupby(final_df.index).mean()
    final_df.dropna(axis=1, how="all", inplace=True)
    print(f"\nData reduction complete.")
    print(f"Reduced data has {len(final_df)} rows.")
    # Prepare final dataframe for saving by making the timestamp a regular column
    df_to_save = final_df.reset_index().rename(columns={"index": "timestamp"})
    # Save to Parquet file
    print(f"Saving reduced data to '{OUTPUT_PARQUET_FILEPATH}'...")
    df_to_save.to_parquet(OUTPUT_PARQUET_FILEPATH)
    # Save to CSV file
    print(f"Saving reduced data to '{OUTPUT_CSV_FILEPATH}'...")
    df_to_save.to_csv(OUTPUT_CSV_FILEPATH, index=False)
    print("Done!")
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Resample and reduce large time-series data from a CSV file."
    )
    parser.add_argument("input_file", help="The path to the input CSV file.")
    args = parser.parse_args()
    process_data_reduction(args.input_file)