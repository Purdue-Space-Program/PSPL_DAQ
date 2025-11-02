import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import os

THEME = "plotly_dark"
MAX_PLOT_POINTS = 50000
# NEW: Smoothing factor for Exponential Moving Average (EMA).
# Lower alpha = more smoothing (slower response). Tune this value!
SMOOTHING_ALPHA = 0.5

def create_interactive_plot(range_name, input_list):
    INPUT_FILE = rf"daq_system/utils/{range_name}/reduced_{range_name}.parquet"
    PLOT_TITLE = input_list[0]
    X_AXIS_LABEL = input_list[1]
    Y1_AXIS_LABEL = input_list[2]
    Y2_AXIS_LABEL = input_list[3]
    OUTPUT_FILENAME = input_list[4]
    START_TIME = input_list[5]
    END_TIME = input_list[6]
    SENSORS_TO_PLOT = input_list[7]
    
    """
    Loads resampled data and creates a high-quality, interactive HTML plot
    with support for dual y-axes and advanced styling, including smoothed slope calculation.
    """
    pio.templates.default = THEME
    print(f"Reading data from '{INPUT_FILE}'...")
    
    # --- Data Loading and Filtering ---
    try:
        df = pd.read_parquet(INPUT_FILE)
    except Exception as e:
        print(
            f"Error: Could not read '{INPUT_FILE}'. Please ensure you have run the data reduction/resampling step first."
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

    # Calculate the time difference (dt) for the denominator of the slope calculation
    dt = df.index.to_series().diff().dt.total_seconds() 
    
    # Filter the DataFrame by time range
    df_filtered = df.loc[START_TIME:END_TIME].copy() # Use .copy() to avoid SettingWithCopyWarning

    if df_filtered.empty:
        print("Error: No data found in the specified time range.")
        return
    
    # --- SLOPE CALCULATION with EMA Filtering ---
    slope_channels = {} 
    for sensor in SENSORS_TO_PLOT:
        if sensor["column"].endswith("_slope"):
            original_col = sensor["column"].replace("_slope", "")
            if original_col in df_filtered.columns:
                 slope_channels[original_col] = sensor["column"]
            else:
                 print(f"Warning: Original column '{original_col}' not found to calculate slope for '{sensor['column']}'. Skipping calculation.")

    
    for original_col, slope_col in slope_channels.items():
        print(f"Applying EMA filter to '{original_col}' (alpha={SMOOTHING_ALPHA}) before calculating slope.")
        
        # 1. APPLY EMA SMOOTHING TO THE ORIGINAL DATA COLUMN
        df_smoothed = df_filtered[original_col].ewm(alpha=SMOOTHING_ALPHA).mean()
        
        # 2. CALCULATE SLOPE (dy/dt) ON THE SMOOTHED DATA
        dy = df_smoothed.diff()
        
        # dt = change in time in seconds
        dt_filtered = dt[df_filtered.index]
        
        # Slope = dy / dt
        df_filtered[slope_col] = dy / dt_filtered
        print(f"Calculated smoothed slope for '{original_col}' as '{slope_col}'.")

    # --- Downsample for Performance ---
    if MAX_PLOT_POINTS and len(df_filtered) > MAX_PLOT_POINTS:
        print(
            f"Data has {len(df_filtered)} points, exceeding the limit of {MAX_PLOT_POINTS}. Downsampling for performance..."
        )
        duration_seconds = (
            df_filtered.index[-1] - df_filtered.index[0]
        ).total_seconds()
        if duration_seconds > 0:
            interval_ms = (duration_seconds / MAX_PLOT_POINTS) * 1000
            resample_rule = (
                f"{max(1, int(interval_ms))}ms"
            )
            df_plot = df_filtered.resample(resample_rule).mean()
            print(
                f"Downsampled to {len(df_plot)} points using a '{resample_rule}' interval."
            )
        else:
            df_plot = df_filtered
    else:
        df_plot = df_filtered
        
    if df_plot.empty:
        print("Error: No data to plot after filtering and downsampling.")
        return
        
    print(f"Plotting {len(df_plot)} data points...")
    
    # --- Create the Interactive Plot ---
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
                f"Warning: Column '{sensor['column']}' not found in data and will be skipped."
            )

    # --- Formatting ---
    fig.update_layout(
        title=dict(text=PLOT_TITLE, font=dict(size=20), x=0.5),
        xaxis_title=X_AXIS_LABEL,
        legend_title_text="Sensors",
    )
    fig.update_yaxes(title_text=Y1_AXIS_LABEL, secondary_y=False)
    fig.update_yaxes(title_text=Y2_AXIS_LABEL, secondary_y=True)

    # --- Saving ---
    try:
        os.makedirs(rf"daq_system/utils/{range_name}", exist_ok=True)
        html_path = rf"daq_system/utils/{range_name}/{range_name}_{OUTPUT_FILENAME}.html"
        fig.write_html(html_path)
        print(f"Successfully saved interactive plot to '{html_path}'")
    except Exception as e:
        print(f"Error: Could not save the plot file. Details: {e}")

if __name__ == '__main__':
    # --- CHANNEL SELECTION: Define the channel whose SLOPE you want to plot ---
    TARGET_CHANNEL = 'PT-OX-04'
    
    # --- PLOT PARAMETERS ---
    PLOT_TITLE = f"Smoothed Slope Analysis for {TARGET_CHANNEL}"
    X_AXIS_LABEL = "Time (UTC)"
    Y1_AXIS_LABEL = "Rate of Change (Units/s)" # Primary Y-axis for slope units
    Y2_AXIS_LABEL = "Secondary Axis (Unused)" 
    OUTPUT_FILENAME = f"{TARGET_CHANNEL}_smoothed_slope"
    START_TIME = None
    END_TIME = None
    
    # --- SENSORS_TO_PLOT: ONLY include the slope column ---
    SENSORS_TO_PLOT = [
        {
            'column': f'{TARGET_CHANNEL}_slope', 
            'name': f'{TARGET_CHANNEL} Smoothed Slope (α={SMOOTHING_ALPHA})', 
            'color': 'red', 
            'yaxis': 'y1' # Plot the slope data on the primary Y-axis
        },
    ]

    # --- EXECUTION ---
    input_list_for_plot = [
        PLOT_TITLE,
        X_AXIS_LABEL,
        Y1_AXIS_LABEL,
        Y2_AXIS_LABEL,
        OUTPUT_FILENAME,
        START_TIME,
        END_TIME,
        SENSORS_TO_PLOT
    ]
    range_name = "10-25-fill-attempts"
    
    create_interactive_plot(range_name, input_list_for_plot)
    pass