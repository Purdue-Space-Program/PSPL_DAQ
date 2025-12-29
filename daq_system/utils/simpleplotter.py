import argparse, os, re
from collections import defaultdict
import numpy as np, pandas as pd, plotly.graph_objects as go, plotly.io as pio
import random
from pathlib import Path

THEME = "plotly_white"

if __debug__:
    # MAX_POINTS_PER_TRACE = 1_000_000
    MAX_POINTS_PER_TRACE = 50_000
else:
    MAX_POINTS_PER_TRACE = 50


use_davids_auto_sensors = True

if use_davids_auto_sensors == False:

    SENSORS_TO_PLOT = [
        # Oxidizer
        {"column": "PT-OX-04", "name": "PT-OX-04", "color": "#391FE0", "yaxis": "y1"},
        {"column": "PT-OX-02", "name": "PT-OX-02", "color": "#4199E1", "yaxis": "y1"},
        {"column": "PT-OX-201", "name": "PT-OX-201", "color": "#97C1E4", "yaxis": "y1"},
        {"column": "PT-OX-202", "name": "PT-OX-202", "color": "#CFD7DE", "yaxis": "y1"},
        {"column": "TC-OX-04", "name": "TC-OX-04", "color": "#2C6CCC", "yaxis": "y2"},
        {"column": "TC-OX-02", "name": "TC-OX-02", "color": "#4491AD", "yaxis": "y2"},
        {"column": "TC-OX-202", "name": "TC-OX-202", "color": "#9BC2DD", "yaxis": "y2"},
        {"column": "PI-OX-02", "name": "PI-OX-02", "color": "#9a28b3", "yaxis": "y4"},
        {"column": "PI-OX-03", "name": "PI-OX-03", "color": "#e662bc", "yaxis": "y4"},
        {"column": "RTD-OX", "name": "RTD-OX", "color": "#286CD1", "yaxis": "y5"},
        # Fuel
        {"column": "PT-FU-04", "name": "PT-FU-04", "color": "#80240B", "yaxis": "y1"},
        {"column": "PT-FU-02", "name": "PT-FU-02", "color": "#A3451D", "yaxis": "y1"},
        {"column": "PT-FU-201", "name": "PT-FU-201", "color": "#C77047", "yaxis": "y1"},
        {"column": "PT-FU-202", "name": "PT-FU-202", "color": "#F6B090", "yaxis": "y1"},
        {"column": "TC-FU-04", "name": "TC-FU-04", "color": "#D42828", "yaxis": "y2"},
        {"column": "TC-FU-02", "name": "TC-FU-02", "color": "#BE3C47", "yaxis": "y2"},
        {"column": "TC-FU-202", "name": "TC-FU-202", "color": "#B34C6C", "yaxis": "y2"},
        {"column": "PI-FU-02", "name": "PI-FU-02", "color": "#e32a33", "yaxis": "y4"},
        {"column": "PI-FU-03", "name": "PI-FU-03", "color": "#bd486f", "yaxis": "y4"},
        {"column": "RTD-FU", "name": "RTD-FU", "color": "#F70D0D", "yaxis": "y5"},
        # He
        {"column": "PT-HE-01", "name": "PT-HE-01", "color": "#2EB613", "yaxis": "y1"},
        {"column": "PT-HE-201", "name": "PT-HE-201", "color": "#87D197", "yaxis": "y1"},
        {"column": "TC-HE-201", "name": "TC-HE-201", "color": "#10842F", "yaxis": "y2"},
        # Other
        {"column": "FMS", "name": "FMS", "color": "#dada0a", "yaxis": "y3"},
    ]

    SENSORS_TO_PLOT_NAMES = [sensor["name"] for sensor in SENSORS_TO_PLOT]

else:

    SENSORS_TO_PLOT_NAMES = [
        "PT_OX_02",
        "PT_OX_04",
        "PT_OX_201",
        "PT_OX_202",

        "TC_OX_02",
        "TC_OX_04",
        "TC_OX_202",
        "TC_OX_201",
        "RTD_OX",

        "PI_OX_02",
        "PI_OX_03",

        "PT_FU_06",
        "PT_FU_04",
        "PT_FU_02",
        "PT_FU_201",
        "PT_FU_202",

        "TC_FU_04",
        "TC_FU_02",
        "TC_FU_202",
        "TC_FU_201",
        "RTD_FU",

        "PI_FU_02",
        "PI_FU_03",
        "PI_FU_04",

        "PT_HE_01",
        "PT_HE_201",
        "TC_HE_201",

        "SV_N2_02_STATE",
        "SV_N2_02",

        "TC_BATTERY",

        "FMS",
    ]

    total_number_fluid_sensors = {
        "OX": 0,
        "FU": 0,
        "HE": 0,
        "N2": 0,
        "WA": 0,   
    }
    
    current_number_fluid_sensors_already_colored = {
        "OX": 0,
        "FU": 0,
        "HE": 0,
        "N2": 0,
        "WA": 0,   
    }
    
    for sensor_name in SENSORS_TO_PLOT_NAMES:
        name_upper = sensor_name.upper()
        
        for fluid_name in total_number_fluid_sensors.keys():
            
            if f"_{fluid_name}" in name_upper:
                total_number_fluid_sensors[fluid_name] += 1
                
                

    def FluidNameToColor(sensor_name, current_number_fluid_sensors_already_colored):
        sensor_name_upper = sensor_name.upper()

        color_selection = "nah"
        
        if color_selection == "random":

            if "_OX" in sensor_name_upper:
                # sensor_color = "#3EABFF"
                # Random shade of blue
                r = random.randint(0, 100)
                g = random.randint(100, 200)
                b = random.randint(200, 255)
                sensor_color = f"#{r:02X}{g:02X}{b:02X}"
            elif "_FU" in sensor_name_upper:
                # sensor_color = "#6D0000"
                # Random shade of red
                r = random.randint(200, 255)
                g = random.randint(50, 150)
                b = random.randint(0, 100)
                sensor_color = f"#{r:02X}{g:02X}{b:02X}"
            elif "_HE" in sensor_name_upper:
                # sensor_color = "#6D0000"
                # Random shade of green
                r = random.randint(0, 100)
                g = random.randint(200, 255)
                b = random.randint(0, 100)
                sensor_color = f"#{r:02X}{g:02X}{b:02X}"
            elif "_N2" in sensor_name_upper:
                # Random shade of purple
                r = random.randint(200, 255)
                g = random.randint(0, 100)
                b = random.randint(200, 255)
                sensor_color = f"#{r:02X}{g:02X}{b:02X}"
            elif "_WA" in sensor_name_upper:
                # Random shade of blue
                r = random.randint(0, 100)
                g = random.randint(100, 200)
                b = random.randint(200, 255)
                sensor_color = f"#{r:02X}{g:02X}{b:02X}"
            elif "FMS" in sensor_name_upper:
                sensor_color = "#DCEB0E"
            else:
                sensor_color = "#949494"

        else:
            
            sensor_color = None
            
            for fluid_name in total_number_fluid_sensors.keys():
                if f"_{fluid_name}" in sensor_name_upper:
                    current_number_fluid_sensors_already_colored[fluid_name] += 1

                    if fluid_name == "OX":
                        min_red = 0
                        max_red = 130
                        min_green = 80
                        max_green = 220
                        min_blue = 180
                        max_blue = 255
                    elif fluid_name == "FU":
                        min_red = 180
                        max_red = 255
                        min_green = 30
                        max_green = 150
                        min_blue = 30
                        max_blue = 150
                    elif fluid_name == "HE":
                        min_red = 0
                        max_red = 100
                        min_green = 100
                        max_green = 255
                        min_blue = 0
                        max_blue = 200
                    elif fluid_name == "N2":
                        min_red = 150
                        max_red = 255
                        min_green = 0
                        max_green = 130
                        min_blue = 150
                        max_blue = 255
                    elif fluid_name == "WA":
                        min_red = 0
                        max_red = 120
                        min_green = 70
                        max_green = 200
                        min_blue = 180
                        max_blue = 255
                    else:
                        raise ValueError("what")
                    
    
                    current_to_total_sensors_colored_ratio = (current_number_fluid_sensors_already_colored[fluid_name]/total_number_fluid_sensors[fluid_name])

                    red = int(min_red + ((max_red-min_red) * current_to_total_sensors_colored_ratio))
                    green = int(max_green + ((min_green-max_green) * current_to_total_sensors_colored_ratio))
                    blue = int(min_blue + ((max_blue-min_blue) * current_to_total_sensors_colored_ratio))
                
                    sensor_color = f"#{red:02X}{green:02X}{blue:02X}"

            if sensor_color is None:
                if "FMS" in sensor_name_upper:
                    sensor_color = "#DCEB0E"
                else:
                    sensor_color = "#949494"
                        
                


        return(sensor_color, current_number_fluid_sensors_already_colored)



    def SensorTypeToAxis(name: str) -> str:
        name_upper = name.upper()

        if "PT_" in name_upper:
            sensor_axis = "y1"
        elif "PI_" in name_upper:
            sensor_axis = "y2"
        elif "TC_" in name_upper:
            sensor_axis = "y3"
        elif "RTD_" in name_upper:
            sensor_axis = "y4"
        elif "FMS" in name_upper:
            sensor_axis = "y5"
        else:
            sensor_axis = "y6"

        return(sensor_axis)

    SENSORS_TO_PLOT = []

    for sensor_name in SENSORS_TO_PLOT_NAMES:
        sensor_color, current_number_fluid_sensors_already_colored = FluidNameToColor(sensor_name, current_number_fluid_sensors_already_colored)
        sensor_axis = SensorTypeToAxis(sensor_name)
        SENSORS_TO_PLOT.append({"column": sensor_name, "name": sensor_name, "color": sensor_color, "yaxis": sensor_axis},)


X_AXIS_LABEL = "Time [H:M:S:milliseconds]"
Y_AXIS_LABELS = {
    "y1": "Pressure [psia]",
    "y2": "Position Indicator [0/1]",
    "y3": "Temperature [°K]",
    "y4": "RTD Voltage [V]",
    "y5": "Mass [lbf]",
    "y6": "unknown sensor [n/a]",
}


DEV5_TIME, DEV6_TIME = "Dev5_BCLS_ai_time", "Dev6_BCLS_ai_time"

# source: https://github.com/Purdue-Space-Program/PSPL_DAQ/tree/525aad863caa300921295408a1d6e08e39765564/daq_system/inputs
DEV5_CHANNELS = [
    # Control Wiring
    "PV_FU_02",
    "PV_OX_02",
    "PV_FU_03",
    "PV_OX_03",
    "SV_BP_01",
    "SV_N2_01",
    "PV_HE_01",
    "PI_HE_01",
    "SV_HE_201",
    "SV_HE_202",
    "SV_HE_201_state",
    "SV_HE_201_state_time",
    "SV_HE_202_state",
    "SV_HE_201_position",
    "SV_HE_202_position",
    "SV_QD_03",
    "DELUGE",
    "SV_QD_01",
    "ACTUATOR",
    "IGNITOR",    
    
    # Data Wiring
    "PT_FU_04",
    "PT_HE_01",
    "PT_OX_04",
    "PT_N2_01",
    "PT_FU_02",
    "PT_OX_02",
    "TC_OX_04",
    "TC_FU_04",
    "TC_OX_02",
    "TC_FU_02",
    "FMS",
    "RTD_OX",
    "RTD_FU",
    "PT_FU_202",
    "PT_OX_202",
    "TC_HE_201",
]

# source: https://github.com/Purdue-Space-Program/PSPL_DAQ/tree/525aad863caa300921295408a1d6e08e39765564/daq_system/inputs
DEV6_CHANNELS = [
    # Control Wiring 
    "PV_FU_04",
    "HS_CAMERA",
    "SV_N2_02",
    "SV_N2_03",
    
    # Data Wiring
    "TC_FMS",
    "TC_OX_202",
    "TC_FU_202",
    "TC_FU_VENT",
    "PT_CHAMBER",
    "PT_FU_06",
]


channels = [
    [DEV5_CHANNELS, DEV5_TIME],
    [DEV6_CHANNELS, DEV6_TIME]
    ]


def VehicleSensorsPairs(csv_columns, already_paired_sensors):
    # print("\nDirectPairs")

    pairs = {}

    for csv_column in csv_columns:

        if csv_column.lower().endswith("_time"):
            sensor_name = re.sub(r"(_time|_TIME)$", "", csv_column)
            
            # avoid pairing time itself
            if ("BCLS_ai" not in sensor_name):
                sensor_name = re.sub(r"(_time|_TIME)$", "", csv_column)

                if sensor_name not in already_paired_sensors:
                    pairs[csv_column] = [sensor_name]


    # ##### compare with old version
    # print (f"\n{pairs}")
    # pairs = None

    # pairs = defaultdict(list)
    # for c in csv_columns:
    #     if c.lower().endswith("_time"):
    #         base = re.sub(r"(_time|_TIME)$", "", c)
    #         if base in csv_columns:
    #             pairs[c].append(base)

    # print (f"\n{pairs}\n")
    # ##### compare with old version

    return pairs


def MakePIPairs(csv_columns, already_paired_sensors):
    # print("\nMakePIPairs")

    pairs = {}

    for csv_column in csv_columns:
        m = re.match(r"^BCLS_di_time_(.+)$", csv_column)

        if m != None:
            sensor_name = m.group(1)
            
            if sensor_name not in already_paired_sensors:
                pairs[csv_column] = [sensor_name]

    # ######### compare with old version
    # print(f"\n{pairs}")
    # pairs = None

    # pairs = defaultdict(list)

    # for csv_column in csv_columns:
    #     # if csv_column == "BCLS_di_time_PI-OX-02":
    #     #     pass
    #     m = re.match(r"^BCLS_di_time_(.+)$", csv_column)
    #     if m and m.group(1) in csv_columns:
    #         pairs[csv_column].append(m.group(1))


    # print(f"\n{pairs}\n")
    # ######### compare with old version

    return pairs


def BCLSPairs(csv_columns, already_paired_sensors):
    # print("\nBCLSPairs")
    

    pairs = defaultdict(list) # dictionary that automatically creates list whenever new key is attempted

    for channel, time in channels:
        if time in csv_columns:
            for sensor_name in channel:
                # if sensor_name == "PT-FU-02":
                #     pass
                    
                    if sensor_name in csv_columns:
                        if sensor_name not in already_paired_sensors:
                            pairs[time].append(sensor_name)


    # ########### compare with old version
    # print(f"New Version: \n{pairs}")
    # pairs = None

    # pairs = defaultdict(list)

    # if DEV5_TIME in csv_columns:
    #     for ch in DEV5_CHANNELS:
    #         if ch in csv_columns:
    #             pairs[DEV5_TIME].append(ch)
    # if DEV6_TIME in csv_columns:
    #     for ch in DEV6_CHANNELS:
    #         if ch in csv_columns:
    #             pairs[DEV6_TIME].append(ch)

    # print(f"\n\nOld Version: \n{pairs}\n")
    # ############ compare with old version

    return(pairs)


def FindGroups(csv_columns):
    groups = defaultdict(list)
    
    already_paired_sensors = {}
    already_paired_sensor_names = []
    pairing_functions = [VehicleSensorsPairs, MakePIPairs, BCLSPairs]
    
    
    for pairing_function in pairing_functions:
        newly_paired_sensors = pairing_function(csv_columns, already_paired_sensor_names)
        
        already_paired_sensors.update(newly_paired_sensors)
        
        for already_paired_sensor_name in already_paired_sensors.values():
            already_paired_sensor_names.append(already_paired_sensor_name[0])

    
    for t, ds in already_paired_sensors.items():
        groups[t].extend(ds)
    return groups



def ConvertCSVToParquet(input_csv: str) -> str:
    """Optimized CSV to Parquet conversion"""
    print("Reading CSV header...")
    header = pd.read_csv(input_csv, nrows=0)
    csv_columns = list(header.columns)
    groups = FindGroups(csv_columns)

    if not groups:
        raise ValueError("No valid time-column groupings found in CSV")

    data_columns_to_plot = {t for t in groups} | {d for ds in groups.values() for d in ds}
    print(
        f"Found {len(groups)} time column groups, {len(data_columns_to_plot)} total columns to process"
    )

    data_columns_to_plot = set(data_columns_to_plot)
    data_columns_to_plot.remove("Dev5_state")
    data_columns_to_plot.remove("Dev6_state")
    
    
    # Read entire CSV at once with optimizations
    print("Reading CSV data...")
    df = pd.read_csv(
        input_csv,
        usecols=set(data_columns_to_plot),
        low_memory=False,
        on_bad_lines="warn",
        engine="c",
    )

    print("Processing time groups...")
    all_frames = []

    for time_column, data_columns in groups.items():
        if time_column not in df.columns:
            continue

        # Create subset with time column and data columns
        subset_cols = [time_column] + [c for c in data_columns if c in df.columns]
        subset = df[subset_cols].copy()

        # Convert time column to datetime
        subset[time_column] = pd.to_datetime(subset[time_column], errors="coerce", utc=True)
        subset = subset.dropna(subset=[time_column])

        if subset.empty:
            continue

        # Set time as index
        subset = subset.set_index(time_column)

        # Handle duplicate indices BEFORE adding to all_frames
        if subset.index.duplicated().any():
            subset = subset.groupby(level=0).mean()

        # Convert all data columns to numeric at once
        for data_column in data_columns:
            if data_column in subset.columns:
                subset[data_column] = pd.to_numeric(subset[data_column], errors="coerce")

        all_frames.append(subset)
        print(f"  Processed {time_column}: {len(subset)} rows, {len(subset.columns)} sensors")

    if not all_frames:
        raise ValueError("No valid data found after processing all groups")

    # Combine all frames with outer join
    print("Combining data frames...")
    combined = pd.concat(all_frames, axis=1, join="outer").sort_index()
    combined = combined.reset_index().rename(columns={"index": "timestamp"})

    # Save to parquet
    base = os.path.splitext(input_csv)[0]
    parquet_path = f"{base}.parquet"

    print(f"Saving to {parquet_path}...")
    combined.to_parquet(parquet_path, index=False, engine="pyarrow")

    print(
        f"✓ Conversion complete: {len(combined)} rows, {len(combined.columns)} columns"
    )
    return parquet_path


def _thin(x, y, maxn):
    if maxn is None:
        raise ValueError

    if len(y) <= maxn:
        return x.values, y.values
    idx = np.linspace(0, len(y) - 1, maxn, dtype=int)
    return x.values[idx], y.values[idx]



# def AssignLegendGroup(sensor_name):
#     """
#     Convert a sensor name like 'PT-OX-04' → 'OX_PT'.
#     If it doesn't match the pattern, return 'OTHER_MISC'.
#     """
#     m = re.match(r"([A-Z]+)-([A-Z]+)", sensor_name)
#     if m:
#         sensor_type, system = m.groups()
#         legend_group_name = f"{system}_{sensor_type}"
#     else:
#         legend_group_name = "OTHER_MISC"
#     return legend_group_name


    # def ChangeVisibility(fig, fluid_abbreviation, current_visibility, should_be_visible):
    #     """Return a list of True/False for each trace depending on whether its name contains system."""
    #     new_visibility = []
    #     for index, trace in enumerate(fig.data):
    #         name = trace.name or ""
    #         if fluid_abbreviation in name:
    #             new_visibility.append(should_be_visible)
    #         else:
    #             new_visibility.append(current_visibility[index])

    #     return new_visibility



def PlotParquet(parquet_path: str, html_out: str, start: str | None, end: str | None):
    pio.templates.default = THEME
    print("Loading parquet file...")
    df = pd.read_parquet(parquet_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    df = df.dropna(subset=["timestamp"]).set_index("timestamp").sort_index()

    if start or end:
        df = df.loc[start:end]

    print(f"Plotting data: {len(df)} rows, {len(df.columns)} columns")
    fig = go.Figure()
    used_axes = []
    traces_added = 0

    for sensor in SENSORS_TO_PLOT:
        column = sensor["column"]
        # if column not in df.columns:
        #     print(f"Warning: Column '{sensor_name}' not found; skipping.")

        try:
            y = pd.to_numeric(df[column], errors="coerce")
            mask = y.notna()
            if not mask.any():
                continue

            x_vals, y_vals = _thin(df.index[mask], y[mask], MAX_POINTS_PER_TRACE)
            y_axis_key = sensor.get("yaxis", "y1").lower()

            if y_axis_key not in used_axes:
                used_axes.append(y_axis_key)


            unit_name = re.search(r"(\[[^\]]+\]|\([^)]+\))\s*$", Y_AXIS_LABELS[y_axis_key]).group(1)
        
                
            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    mode="lines",
                    name=sensor.get("name", column),
                    line=dict(color=sensor.get("color")),
                    yaxis=y_axis_key,
                    visible=True,
                    hovertemplate=f"%{{y:.2f}} {unit_name}",
                )
            )
            traces_added += 1
            print(f"✅ Added trace: {sensor.get('name', column)} ({len(y_vals)} points)")
            
        except KeyError:
            print(f"🚫 {column} not found in data!")



    fig.update_layout(
        
        title = f"{Path(parquet_path).with_suffix("").name}",
        
        yaxis=dict(title="Pressure [psia]", visible=True),

        yaxis2=dict(title="Position Indicator [0/1]",
                    overlaying="y", side="right",
                    visible=True),

        yaxis3=dict(title="Temperature [°K]",
                    anchor="free", overlaying="y",
                    side="right", position=0.95,
                    visible=True),

        yaxis4=dict(title="RTD Voltage (V)",
                    anchor="free", overlaying="y",
                    side="right", position=0.90,
                    visible=True),

        yaxis5=dict(title="Mass (lbf)",
                    anchor="free", overlaying="y",
                    side="right", position=0.85,
                    visible=True),


        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(
                        label="Toggle OX",
                        method="update",
                        args=[{}, {}],
                        name="btn_ox",
                    ),
                    dict(
                        label="Toggle FU",
                        method="update",
                        args=[{}, {}],
                        name="btn_fu",
                    ),
                    dict(
                        label="Toggle HE",
                        method="update",
                        args=[{}, {}],
                        name="btn_he",
                    ),
                    dict(
                        label="Toggle PT",
                        method="update",
                        args=[{}, {}],
                        name="btn_pt",
                    ),
                    dict(
                        label="Toggle TC",
                        method="update",
                        args=[{}, {}],
                        name="btn_tc",
                    ),
                    dict(
                        label="Toggle RTD",
                        method="update",
                        args=[{}, {}],
                        name="btn_rtd",
                    ),
                    dict(
                        label="Toggle PI",
                        method="update",
                        args=[{}, {}],
                        name="btn_pi",
                    ),
                    dict(
                        label="Toggle FMS",
                        method="update",
                        args=[{}, {}],
                        name="btn_fms",
                    ),
                    dict(
                        label="Show ALL",
                        method="update",
                        args=[{}, {}],
                        name="btn_all",
                    ),
                ],
                direction="down",
                pad=dict(r=10, t=10),
                bgcolor="#333",
                font=dict(color="white"),
            )
        ]
    )

    def _layout_axis_key(k):
        return "yaxis" if k.lower() == "y1" else f"yaxis{int(k[1:])}"


    def export_plot_with_dynamic_buttons(fig, path, div_id="my_fig"):
        """Export Plotly HTML with JS that adds dynamic group toggling."""

        # Step 1 — save HTML normally
        fig.write_html(path,
                       include_plotlyjs="cdn",
                       full_html=True,
                       div_id=div_id)


        # Step 2 — JavaScript code for real-time group toggle
        js_code = """
                <script>
                (function(){
                    function toggleGroup(tag) {
                    const gd = document.getElementById("my_fig");
                    if (!gd) return;

                    const data = gd.data;

                    // Determine which traces belong to this group
                    const groupIdx = [];
                    for (let i = 0; i < data.length; i++) {
                        if (data[i].name && data[i].name.includes(tag)) {
                            groupIdx.push(i);
                        }
                    }

                    if (tag === "ALL") {
                        // Show everything
                        Plotly.restyle(gd, {visible: true});
                        return;
                    }

                    // Get current group visibility (treat undefined as visible)
                    const groupVis = groupIdx.map(i =>
                        (data[i].visible === undefined || data[i].visible)
                    );

                    // If ANY are visible → turn ALL off
                    // If ALL are hidden → turn ALL on
                    const target = groupVis.some(v => v) ? false : true;

                    // Build final visibility array
                    let vis = data.map(t => t.visible === "legendonly" ? false : t.visible !== false);

                    for (const idx of groupIdx) {
                        vis[idx] = target;
                    }

                    Plotly.restyle(gd, {visible: vis});
                    }


                    // Helper: find a descendant element whose trimmed textContent equals label
                    function findElementByExactText(root, label) {
                        const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
                        let node;
                        while (node = walker.nextNode()) {
                            const txt = (node.textContent || "").trim();
                            if (txt === label) return node;
                        }
                        return null;
                    }

                    // Attach handlers once the buttons exist. Use MutationObserver to detect rendering.
                    function attachWhenReady() {
                    const gd = document.getElementById("my_fig");
                    if (!gd) {
                        console.warn("toggleGroup: plot div not found (#my_fig)");
                        return;
                    }

                    const labels = [
                        "Toggle OX",
                        "Toggle FU",
                        "Toggle HE",
                        "Toggle PT",
                        "Toggle TC",
                        "Toggle RTD",
                        "Toggle PI",
                        "Toggle FMS",
                        "Show ALL",
                    ];

                    const handlers = [
                        () => toggleGroup("_OX"),
                        () => toggleGroup("_FU"),
                        () => toggleGroup("_HE"),
                        () => toggleGroup("PT_"),
                        () => toggleGroup("TC_"),
                        () => toggleGroup("RTD_"),
                        () => toggleGroup("PI_"),
                        () => toggleGroup("FMS"),
                        () => toggleGroup("ALL"),
                    ];

                    let attached = 0;
                    const timeoutAt = Date.now() + 3000; // try up to 3s

                    const tryAttach = () => {
                        for (let i = 0; i < labels.length; i++) {
                            const label = labels[i];
                            const el = findElementByExactText(gd, label);
                            if (el && !el.__toggle_attached) {
                                el.addEventListener("click", handlers[i]);
                                el.__toggle_attached = true;
                                attached++;
                                console.log("toggleGroup: attached handler to button:", label, el);
                            }
                        }
                        if (attached === labels.length) {
                            console.log("toggleGroup: all handlers attached");
                            observer.disconnect();
                            return;
                        }
                        if (Date.now() > timeoutAt) {
                            console.warn("toggleGroup: timed out waiting for buttons; attached:", attached);
                            observer.disconnect();
                        }
                    };

                    // Try immediately in case elements are already present
                    tryAttach();

                    // Observe DOM changes to catch the buttons when Plotly renders them
                    const observer = new MutationObserver(() => {
                        tryAttach();
                    });
                    observer.observe(gd, { childList: true, subtree: true });
                }

                if (document.readyState === "complete" || document.readyState === "interactive") {
                    setTimeout(attachWhenReady, 50);
                } else {
                    window.addEventListener("DOMContentLoaded", () => setTimeout(attachWhenReady, 50));
                }
                })();
                </script>
                """

        hide_unused_axis_js = """
        <script>
        document.addEventListener('DOMContentLoaded', () => {
            const graph = document.getElementById('my_fig');
            if (!graph) return;

            // --- ADD THIS THROTTLE FUNCTION ---
            function throttle(fn, wait) {
                let last = 0;
                return function(...args) {
                    const now = Date.now();
                    if (now - last >= wait) {
                        last = now;
                        fn.apply(this, args);
                    }
                };
            }

            // --- MOVE YOUR HIDE FUNCTION INTO ITS OWN WRAPPER ---
            function hideUnusedAxes() {
                const gd = graph._fullLayout;
                const data = graph.data;

                const axesUsed = {};

                data.forEach(trace => {
                    const isVisible = !(trace.visible === false || trace.visible === "legendonly");
                    // Convert trace.yaxis ("y", "y2", ...) into layout key ("yaxis", "yaxis2", ...)
                    let axis = trace.yaxis || 'y';
                    if (axis === 'y') {
                        axis = 'yaxis';
                    } else {
                        axis = axis.replace('y', 'yaxis');
                    }

                    if (isVisible) axesUsed[axis] = true;
                });

                const update = {};

            ['yaxis', 'yaxis2', 'yaxis3', 'yaxis4', 'yaxis5'].forEach(key => {
                if (gd[key]) {
                    update[key + '.visible'] = !!axesUsed[key];
                }
            });

                Plotly.relayout(graph, update);
            }

            // --- REPLACE YOUR ORIGINAL LISTENER WITH THROTTLED VERSION ---
            graph.on('plotly_restyle', throttle(hideUnusedAxes, 150));
        });
        </script>
        """


        theme_toggle_js = """
        <script>
        (function() {
            const btn = document.createElement("input");
            btn.type = "checkbox";
            btn.id = "themeToggle";
            btn.style.position = "fixed";
            btn.style.top = "10px";
            btn.style.left = "10px";
            btn.style.zIndex = "9999";
            btn.title = "Toggle Dark Mode";

            const lbl = document.createElement("label");
            lbl.htmlFor = "themeToggle";
            lbl.innerText = "🌞/🌙";
            lbl.style.position = "fixed";
            lbl.style.top = "12px";
            lbl.style.left = "40px";
            lbl.style.color = "black";
            lbl.style.fontFamily = "sans-serif";
            lbl.style.fontSize = "25px";
            lbl.style.cursor = "pointer";
            lbl.style.zIndex = "9999";

            document.body.appendChild(lbl);
            document.body.appendChild(btn);

            btn.addEventListener("change", () => {
                const gd = document.getElementById("my_fig");
                if (!gd) return;

                const isDark = btn.checked;
                const newTemplate = isDark ? "plotly_dark" : "plotly_white";

                const layoutUpdate = {
                    template: newTemplate,
                    paper_bgcolor: isDark ? "#111" : "#fff",
                    plot_bgcolor: isDark ? "#111" : "#fff",
                    font: { color: isDark ? "#eee" : "#000" },
                };

                console.log("Switching theme to:", newTemplate);
                Plotly.react(gd, gd.data, Object.assign({}, gd.layout, layoutUpdate));

                // Change page background and label color too
                document.body.style.backgroundColor = layoutUpdate.paper_bgcolor;
                lbl.style.color = layoutUpdate.font.color;
            });
        })();
        </script>
        """
        
        
        
        color_picker_js = """
        <script>
        (function() {
            // Wait for the plot div to exist
            const gd = document.getElementById("my_fig");
            if (!gd) return;

            // --- Create the panel container ---
            const panel = document.createElement("div");
            panel.id = "traceColorPanel";
            panel.style.position = "fixed";
            panel.style.bottom = "10px";
            panel.style.right = "10px";
            panel.style.padding = "10px";
            panel.style.backgroundColor = "rgba(255,255,255,0.9)";
            panel.style.border = "1px solid #888";
            panel.style.borderRadius = "5px";
            panel.style.fontFamily = "sans-serif";
            panel.style.fontSize = "8px";
            panel.style.zIndex = "9999";
            panel.style.textAlign = "center"; // center heading
            panel.innerHTML = '<span style="font-size:12px; font-weight:bold;">Line Colors</span><br>';

            // Optional: check for dark mode toggle
            const themeToggle = document.getElementById("themeToggle");

            function applyPanelTheme() {
                if (themeToggle && themeToggle.checked) {
                    // Dark mode
                    panel.style.backgroundColor = "rgba(30,30,30,0.9)";
                    panel.style.border = "1px solid #aaa";
                    panel.style.color = "#eee";
                } else {
                    // Light mode
                    panel.style.backgroundColor = "rgba(255,255,255,0.9)";
                    panel.style.border = "1px solid #888";
                    panel.style.color = "#000";
                }
            }

            // Call it once to set initial theme
            applyPanelTheme();

            // Update panel when theme changes
            if (themeToggle) {
                themeToggle.addEventListener("change", () => {
                    applyPanelTheme();
                    updatePanel();
                });
            }


            // --- Add a row for each visible trace ---
            gd.data.forEach((trace, i) => {
                const isVisible = trace.visible !== false && trace.visible !== "legendonly";
                if (!isVisible) return;

                const row = document.createElement("div");
                row.style.marginBottom = "5px";
                row.style.display = "flex";
                row.style.alignItems = "left";
                row.style.justifyContent = "left";

                const label = document.createElement("span");
                label.textContent = trace.name;
                label.style.marginRight = "5px";

                const input = document.createElement("input");
                input.type = "color";
                input.value = trace.line.color || "#757575";
                input.title = "Change line color";

                // Make the color box small
                input.style.width = "14px";
                input.style.height = "8px";
                input.style.padding = "0";
                input.style.marginLeft = "5px";
                input.style.border = themeToggle && themeToggle.checked ? "1px solid #eee" : "1px solid #000";
                input.style.verticalAlign = "middle";
                input.style.cursor = "pointer";

                input.addEventListener("input", () => {
                    Plotly.restyle(gd, {"line.color": input.value}, [i]);
                });

                row.appendChild(label);
                row.appendChild(input);
                panel.appendChild(row);
            });

            // Attach panel to body
            document.body.appendChild(panel);

            // Adjust Plotly layout margins to make room for the panel
            const panelWidth = panel.offsetWidth + 20;
            Plotly.relayout(gd, {margin: {r: panelWidth}});

            // Optional: Update panel if traces are toggled or restyled
            function updatePanel() {
                // Clear previous panel rows
                panel.innerHTML = '<span style="font-size:12px; font-weight:bold;">Line Colors</span><br>';
                gd.data.forEach((trace, i) => {
                    const isVisible = trace.visible !== false && trace.visible !== "legendonly";
                    if (!isVisible) return;

                    const row = document.createElement("div");
                    row.style.marginBottom = "5px";
                    row.style.display = "flex";
                    row.style.alignItems = "left";
                    row.style.justifyContent = "left";

                    const label = document.createElement("span");
                    label.textContent = trace.name;
                    label.style.marginRight = "5px";

                    const input = document.createElement("input");
                    input.type = "color";
                    input.value = trace.line.color || "#757575";
                    input.title = "Change trace color";

                    input.style.width = "14px";
                    input.style.height = "8px";
                    input.style.padding = "0";
                    input.style.marginLeft = "5px";
                    input.style.border = themeToggle && themeToggle.checked ? "1px solid #eee" : "1px solid #000";
                    input.style.verticalAlign = "middle";
                    input.style.cursor = "pointer";

                    input.addEventListener("input", () => {
                        Plotly.restyle(gd, {"line.color": input.value}, [i]);
                    });

                    row.appendChild(label);
                    row.appendChild(input);
                    panel.appendChild(row);
                });

                // Adjust margins again
                const panelWidth = panel.offsetWidth + 20;
                Plotly.relayout(gd, {margin: {r: panelWidth}});
            }

            gd.on('plotly_restyle', () => setTimeout(updatePanel, 50));
        })();
        </script>
        """



        # Step 3 — append JS before </body>
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()

        html = html.replace("</body>", js_code + theme_toggle_js + hide_unused_axis_js + color_picker_js + "\n</body>")

        # Step 4 — write modified HTML back
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)


    if traces_added == 0:
        print("WARNING: No traces were added to the plot!")
        print(f"Available columns in data: {list(df.columns)}")
        print(f"Requested sensors: {[s['column'] for s in SENSORS_TO_PLOT]}")

    fig.update_layout(xaxis=dict(title=X_AXIS_LABEL), hovermode="x unified")
    used_axes.sort(key=lambda a: int(a[1:]) if a[1:].isdigit() else 1)

    step = 0.14 / max(1, len(used_axes) - 1) if len(used_axes) > 1 else 0

    for i, y_axis_key in enumerate(used_axes):

        y_axis_label = Y_AXIS_LABELS.get(y_axis_key, y_axis_key)
        if y_axis_key == "y1":
            dictionary = dict(title=dict(text=y_axis_label),
                              side="left",
                              position=0.0,
                              showgrid=True)
        else:
            side = "right" if i % 2 else "left"
            pos = (1 - (i // 2) * step) if side == "right" else ((i // 2 + 1) * step)
            pos = max(0.02, min(0.98, pos))
            dictionary = dict(
                title=dict(text=y_axis_label),
                overlaying="y",
                side=side,
                position=pos,
                showgrid=False,
            )

        layout_key = _layout_axis_key(y_axis_key)
        fig.update_layout(**{layout_key: dictionary})

    print(f"Saving plot to {html_out}...")
    export_plot_with_dynamic_buttons(fig, html_out, div_id="my_fig")
    print(f"✓ Plot saved with {traces_added} traces")


def main():

    DEFAULT_PATH = "utils/test_data_truncated.csv"
    _SENTINEL = object()

    ap = argparse.ArgumentParser()

    ap.add_argument(
        "input_path",
        nargs="?",
        default=_SENTINEL,
    )

    ap.add_argument("--start", default=None)
    ap.add_argument("--end", default=None)

    args = ap.parse_args()


    if args.input_path is _SENTINEL:
        # user did NOT provide input_path
        print(f"\nWARNING!!!!!!!!!!! No input file provided, using default input path: {DEFAULT_PATH}\n")
        args.input_path = DEFAULT_PATH

    path_to_input_file = args.input_path
    input_file_name = os.path.splitext(os.path.basename(path_to_input_file))[0]

    if path_to_input_file.lower().endswith(".csv"):
        parquet_path = ConvertCSVToParquet(path_to_input_file)
    elif path_to_input_file.lower().endswith((".parquet", ".pq")):
        parquet_path = path_to_input_file
    else:
        raise SystemExit("input must be .csv or .parquet")

    range_name = "12-17-Hotfire"
    html_output_path = rf"daq_system/utils//{range_name}/datadump_{range_name}.html"
        
    PlotParquet(parquet_path, html_output_path, args.start, args.end)
    print(f"\n✓ Complete! Plot saved to: {html_output_path}")


if __name__ == "__main__":
    main()