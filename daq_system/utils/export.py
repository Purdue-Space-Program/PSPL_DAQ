from daq_system.config.settings import DAQConfig, DEFAULT_DEVICE_PATHS
from colorama import Fore, Style
import synnax as sy
import pandas as pd
import colorama
import yaml
import csv

pd.set_option("display.float_format", "{:.0f}".format)

def main(channel_range: str):
    colorama.init()

    client = sy.Synnax(
        host=DAQConfig.host,
        port=DAQConfig.port,
        username=DAQConfig.username,
        password=DAQConfig.password,
    )

    try:
        the_range = client.ranges.retrieve(name=channel_range)
    except sy.exceptions.QueryError:
        print(Style.BRIGHT + Fore.RED + 'That range does not exist!!' + Style.RESET_ALL)
        return

    output_df = pd.DataFrame()

    # File of channels to export.
    with open('daq_system/utils/export.yaml') as f:
        yaml_data = yaml.safe_load(f)

        # Search for channel in configs.
        for ch in yaml_data['channels']:

            # All DAQ configs.
            for i in DEFAULT_DEVICE_PATHS.values():
                ai_excel_file = pd.read_excel(i.data_wiring, sheet_name='AI_slope-offset')

                # Check for channel name within config.
                for idx, name in enumerate(ai_excel_file['Name']):
                    b = ai_excel_file.loc[idx]
                    if name == ch:
                        for b in the_range[name]:
                            if "BCLS_ai_time" not in output_df.columns:
                                output_df["BCLS_ai_time"] = pd.Series(the_range["BCLS_ai_time"]).reset_index(drop=True)
                            output_df[name] = pd.Series(b.read()).reset_index(drop=True)

                di_excel_file = pd.read_excel(i.data_wiring, sheet_name='DI')

                for idx, name in enumerate(di_excel_file['Name']):
                    b = di_excel_file.loc[idx]
                    if name == ch:
                        for b in the_range[name]:
                            if f"BCLS_di_time_f{name}" not in output_df.columns:
                                output_df[f"BCLS_di_time_{name}"] = pd.Series(the_range[f"BCLS_di_time_{name}"]).reset_index(drop=True)
                            output_df[name] = pd.Series(b.read()).reset_index(drop=True)

    print(output_df)
    output_df.to_csv(f"datadump_{range}.csv")

if __name__ == '__main__':
    range = input('Range you wish to export: ')
    main(range)
