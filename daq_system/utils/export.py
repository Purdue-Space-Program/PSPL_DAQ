from daq_system.config.settings import DAQConfig, DEFAULT_DEVICE_PATHS
from colorama import Fore, Style
import synnax as sy
import pandas as pd
import colorama
import yaml
import csv
import os

pd.set_option("display.float_format", "{:.20f}".format)

def safe_series_retrieve(the_range, channel_key, dtype=None):
    """Safely retrieves a series from the Synnax range, handling IndexError if empty."""
    try:
        data = the_range[channel_key]
        if not data or len(data) == 0:
            print(Fore.YELLOW + f"WARNING: Data for '{channel_key}' is empty (length 0). Skipping." + Style.RESET_ALL)
            return None
        
        series = pd.Series(data).reset_index(drop=True)
        if dtype:
            series = series.astype(dtype)
        return series
    except sy.exceptions.KeyError:
        print(Fore.YELLOW + f"WARNING: Channel '{channel_key}' not found in range. Skipping." + Style.RESET_ALL)
        return None
    except IndexError:
        # This catches the deep synnax error from calling len(data) == 0, though safe_series_retrieve should prevent it.
        # It's a fallback for safety.
        print(Fore.YELLOW + f"WARNING: An IndexError occurred for '{channel_key}', data likely empty. Skipping." + Style.RESET_ALL)
        return None


def export_data(range_name):
    colorama.init()

    export_client = sy.Synnax(
        host=DAQConfig.host,
        port=DAQConfig.port,
        username=DAQConfig.username,
        password=DAQConfig.password,
    )

    output_df = pd.DataFrame()

    # File of channels to export.
    with open('daq_system/utils/export.yaml') as f:
        yaml_data = yaml.safe_load(f)
        os.makedirs(rf"daq_system/utils/{range_name}", exist_ok=True)
        try:
            the_range = export_client.ranges.retrieve(name = range_name)
        except sy.exceptions.QueryError:
            print(Style.BRIGHT + Fore.RED + 'That range does not exist!!' + Style.RESET_ALL)
            return

        # -------------------------------------------------------------
        # ANALOG INPUT (AI) CHANNELS
        # -------------------------------------------------------------
        for j in DEFAULT_DEVICE_PATHS.values():
            ai_excel_file = pd.read_excel(j.data_wiring, sheet_name='AI_slope-offset')
            di_excel_file = pd.read_excel(j.data_wiring, sheet_name='DI')
            do_excel_file = pd.read_excel(j.control_wiring, sheet_name = 'DO')
            
            device_name = next(
                key for key, value in DEFAULT_DEVICE_PATHS.items() if value == j
            )

            print(device_name)
            for i, ch_name in enumerate(ai_excel_file['Name']):
                row = ai_excel_file.iloc[i]
                if ch_name in yaml_data['channels']:
                    # Retrieve the main AI time series once
                    ai_time_key = f"{device_name}_BCLS_ai_time"
                    if ai_time_key not in output_df.columns:
                        time_series = safe_series_retrieve(the_range, ai_time_key, dtype='int64')
                        if time_series is not None:
                             output_df[ai_time_key] = time_series
                             print(ai_time_key)

                    # Retrieve the AI data series
                    data_series = safe_series_retrieve(the_range, ch_name)
                    if data_series is not None:
                        output_df[ch_name] = data_series
                        print(ch_name)


            # -------------------------------------------------------------
            # DIGITAL INPUT (DI) CHANNELS
            # -------------------------------------------------------------
            for i, ch_name in enumerate(di_excel_file['Name']):
                row = di_excel_file.iloc[i]
                if ch_name in yaml_data['channels']:
                    # Retrieve DI Time
                    di_time_key = f"BCLS_di_time_{ch_name}"
                    time_series = safe_series_retrieve(the_range, di_time_key, dtype='int64')
                    if time_series is not None:
                         output_df[di_time_key] = time_series
                         print(di_time_key)

                    # Retrieve DI Data
                    data_series = safe_series_retrieve(the_range, ch_name)
                    if data_series is not None:
                        output_df[ch_name] = data_series
                        print(ch_name)

            #Do state channels
            for i, ch_name in enumerate(do_excel_file['Name']):
                row = do_excel_file.iloc[i]
                if ch_name in yaml_data['channels']:
                    # Retrieve State Time
                    do_time_key = f"{device_name}_state_time"
                    time_series = safe_series_retrieve(the_range, do_time_key, dtype='int64')
                    if time_series is not None:
                        output_df[do_time_key] = time_series
                        print(do_time_key)

                    # Retrieve DO Data
                    state_data_series = safe_series_retrieve(the_range, f'{ch_name}_state')
                    if state_data_series is not None:
                        output_df[f'{ch_name}_state'] = 1 - state_data_series
                        print(f'{ch_name}_state')
        
        # -------------------------------------------------------------
        # AVIONICS CHANNELS
        # -------------------------------------------------------------
        avi_excel_file = pd.read_excel('daq_system/inputs/CMS_Avionics_Channels.xlsx', sheet_name='telem_channels')
        for ch_name in avi_excel_file['Name']:
            if ch_name in yaml_data['channels']:
                # Retrieve Avionics Time
                avi_time_key = f"{ch_name}_time"
                time_series = safe_series_retrieve(the_range, avi_time_key)
                if time_series is not None:
                    output_df[avi_time_key] = time_series
                    print(avi_time_key)
                    
                # Retrieve Avionics Data
                data_series = safe_series_retrieve(the_range, ch_name)
                if data_series is not None:
                    output_df[ch_name] = data_series
                    print(ch_name)

    print(output_df)
    
    output_df.to_csv(rf"daq_system/utils//{range_name}/datadump_{range_name}.csv", index=False, float_format='%.19f')

if __name__ == '__main__':
    range_name = "Test"
    export_data(range_name)