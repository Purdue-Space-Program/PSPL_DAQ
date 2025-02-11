import synnax as sy
from typing import Optional


class ChannelFactory:
    """Factory class for creating Synnax channels"""

    def __init__(self, client: sy.Synnax):
        self.client = client

    def create_timestamp_channel(self, name: str) -> sy.Channel:
        """Create a timestamp channel"""
        return self.client.channels.create(
            name=name,
            is_index=True,
            data_type=sy.DataType.TIMESTAMP,
            retrieve_if_name_exists=True,
        )

    def create_data_channel(self,
                            name: str,
                            data_type: sy.DataType,
                            index_key: str,
                            rate: int,
                            units: Optional[str] = None) -> sy.Channel:
        """Create a data channel"""
        # Base channel configuration
        channel_config = {
            "name": name,
            "data_type": data_type,
            "retrieve_if_name_exists": True,
            "index": index_key,
            "rate": rate
        }

        # Add units only if specified (for analog channels)
        if units is not None:
            channel_config["units"] = units

        return self.client.channels.create(**channel_config)