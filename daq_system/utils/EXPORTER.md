# Synnax Data Exporter

## How to Use
### Channel List
Declare the channels you want data from inside of `daq_system/utils/export.yaml`:
```yaml
channels:
  - RTD-OX
  - RTD-FU
  - PI-FU-03
```
Time channels aren't necessary as the exporter will parse them out for you!


### Environment
Make sure you're inside of the virtual environment:
```
uv sync
source .venv/bin/activate
```

### Running
```
python3 -m daq_system.utils.export
```

It will then prompt you for the Synnax data ranges you want to export from:
```
Range you wish to export: 
```
You should type out the exact range name.

### Output
The file will be named `datadump_<RANGE_NAME>.csv`.
Make sure you note the particular time channel a channel uses.
