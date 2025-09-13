from daq_system.config.settings import DAQConfig, DEFAULT_DEVICE_PATHS
from colorama import Fore, Style
import synnax as sy
import pandas as pd
import colorama
import yaml
import csv

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

    output_df = pd.DataFrame(the_range.BCLS_ai_time, columns=['BCLS_ai_time'])

    # File of channels to export.
    with open('daq_system/utils/export.yaml') as f:
        yaml_data = yaml.safe_load(f)

        # Search for channel in configs.
        for ch in yaml_data['channels']:

            # All DAQ configs.
            for i in DEFAULT_DEVICE_PATHS.values():
                excel_file = pd.read_excel(i.data_wiring, sheet_name='AI_slope-offset')

                # Check for channel name within config.
                for idx, name in enumerate(excel_file['Name']):
                    b = excel_file.loc[idx]
                    if name == ch:
                        for b in the_range[name]:
                            output_df[name] = b.read()

    output_df.to_csv()

if __name__ == '__main__':
    range = input('Range(s) you wish to export: ')
    main(range)
