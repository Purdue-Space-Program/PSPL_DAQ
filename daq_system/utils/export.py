from daq_system.config.settings import DAQConfig, DEFAULT_DEVICE_PATHS
from colorama import Fore, Style
import synnax as sy
import pandas as pd
import colorama
import yaml
import csv

pd.set_option("display.float_format", "{:.20f}".format)

def main():
    colorama.init()

    client = sy.Synnax(
        host=DAQConfig.host,
        port=DAQConfig.port,
        username=DAQConfig.username,
        password=DAQConfig.password,
    )

    output_df = pd.DataFrame()

    # File of channels to export.
    with open('daq_system/utils/export.yaml') as f:
        yaml_data = yaml.safe_load(f)

        try:
            the_range = client.ranges.retrieve(name=yaml_data['range'])
        except sy.exceptions.QueryError:
            print(Style.BRIGHT + Fore.RED + 'That range does not exist!!' + Style.RESET_ALL)
            return

        for i in DEFAULT_DEVICE_PATHS.values():
            ai_excel_file = pd.read_excel(i.data_wiring, sheet_name='AI_slope-offset')
            di_excel_file = pd.read_excel(i.data_wiring, sheet_name='DI')

            for i, ch_name in enumerate(ai_excel_file['Name']):
                row = ai_excel_file.iloc[i]
                if ch_name in yaml_data['channels']:
                    if "BCLS_ai_time" not in output_df.columns:
                        output_df["BCLS_ai_time"] = pd.Series(the_range["BCLS_ai_time"]).astype('int64').reset_index(drop=True)

                    data = the_range[ch_name]

                    output_df[ch_name] = pd.Series(data).reset_index(drop=True)

            for i, ch_name in enumerate(di_excel_file['Name']):
                row = di_excel_file.iloc[i]
                if ch_name in yaml_data['channels']:
                    output_df[f"BCLS_di_time_{ch_name}"] = pd.Series(the_range[f"BCLS_di_time_{ch_name}"]).astype('int64').reset_index(drop=True)

                    data = the_range[ch_name]

                    output_df[ch_name] = pd.Series(data).reset_index(drop=True)
        
        avi_excel_file = pd.read_excel('daq_system/inputs/CMS_Avionics_Channels.xlsx', sheet_name='telem_channels')
        for ch_name in avi_excel_file['Name']:
            if ch_name in yaml_data['channels']:
                output_df[f"{ch_name}_time"] = pd.Series(the_range[f"{ch_name}_time"]).reset_index(drop=True)
                output_df[ch_name] = pd.Series(the_range[ch_name]).reset_index(drop=True)
                    
    print(output_df)
    output_df.to_csv(f"datadump_{yaml_data['range']}.csv", index=False, float_format='%.19f')

if __name__ == '__main__':
    main()
