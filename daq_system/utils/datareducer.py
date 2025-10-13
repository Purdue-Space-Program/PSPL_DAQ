
import pandas as pd
import re
import os
import argparse
from collections import defaultdict
# uv pip install pandas pyarrow fastparquet

def find_column_groups(columns):
    time_col_map = defaultdict(list)
    data_cols_with_time = set()
    time_cols = [c for c in columns if "time" in c.lower()]
    for t_col in time_cols:
        base_name = re.sub(r"(_time|_TIME)", "", t_col)
        base_name_short = base_name.split("_")[-1]
        for d_col in columns:
            if d_col == base_name or d_col == base_name_short:
                if d_col not in data_cols_with_time:
                    time_col_map[t_col].append(d_col)
                    data_cols_with_time.add(d_col)
    # Handle the special 'BCLS_ai_time' case which covers multiple columns
    if "Dev5_BCLS_ai_time" in time_cols:
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
            "FMS",
            "RTD-OX",
            "RTD-FU",
            "TC-HE-201",
            "PT-FU-202",
            "PT-OX-202",
            "TC-HE-201",
            
        ]
        for col in ai_cols:
            if col in columns and col not in data_cols_with_time:
                time_col_map["Dev5_BCLS_ai_time"].append(col)
                data_cols_with_time.add(col)
    # Identify any columns that weren't grouped
    unmapped_cols = set(columns) - data_cols_with_time - set(time_cols)
    if unmapped_cols:
        print(
            f"Warning: The following columns could not be mapped to a time column and will be ignored: {unmapped_cols}"
        )
    return time_col_map

def process_data_reduction(input_filepath, range_name):
    RESAMPLE_FREQ = "10ms"
    CHUNKSIZE = 1_000_000
    os.makedirs(rf"daq_system/utils/{range_name}", exist_ok=True)
    OUTPUT_CSV_FILEPATH = rf"daq_system/utils/{range_name}/reduced_{range_name}.csv"
    OUTPUT_PARQUET_FILEPATH = rf"daq_system/utils/{range_name}/reduced_{range_name}.parquet"
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
    process_data_reduction(r"C:\Users\nmaso\OneDrive - purdue.edu\Desktop\datadump_10-10 Hotfire Attempt AI Data.csv", "10-10 Hotfire Attempt AI Data")