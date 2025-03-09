import synnax as sy
from typing import Optional


class ChannelFactory:
    """Factory class for creating Synnax channels"""

    def __init__(self, client: sy.Synnax):
        self.client = client

    def create_timestamp_channel(self, name: str) -> sy.Channel:
        """Create a timestamp channel that can be used as an index"""
        return self.client.channels.create(
            name=name,
            is_index=True,
            data_type=sy.DataType.TIMESTAMP,
            retrieve_if_name_exists=True,
        )

    def create_data_channel(
        self, name: str, data_type: sy.DataType, index_key: str
    ) -> sy.Channel:
        """Create a data channel with an index"""
        return self.client.channels.create(
            name=name
            data_type=data_type,
            index=index_key,
            retrieve_if_name_exists=True,
        )

    def create_virtual_channel(self, name: str, data_type: sy.DataType) -> sy.Channel:
        """Create a virtual channel (for commands)"""
        return self.client.channels.create(
            name=name,
            data_type=data_type,
            retrieve_if_name_exists=True,
            virtual=True,
        )
