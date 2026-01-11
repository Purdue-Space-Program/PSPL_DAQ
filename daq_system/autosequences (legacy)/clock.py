import synnax as sy

client = sy.Synnax(
    host='sedsdaq.ecn.purdue.edu',
    port=2701,
    username='Bill',
    password='Bill',
)

def main():
    clock_index = client.channels.create(
        name='T_CLOCK_INDEX',
        is_index=True,
        data_type=sy.DataType.TIMESTAMP,
        retrieve_if_name_exists=True,
    )
    clock = client.channels.create(
        name='T_CLOCK_MS',
        data_type='int64',
        index=clock_index.key,
        retrieve_if_name_exists=True,
    )
    clock_sec = client.channels.create(
        name='T_CLOCK_SEC',
        data_type='int64',
        index=clock_index.key,
        retrieve_if_name_exists=True,
    )
    clock_min = client.channels.create(
        name='T_CLOCK_MIN',
        data_type='int64',
        index=clock_index.key,
        retrieve_if_name_exists=True,
    )
    clock_string = client.channels.create(
        name='T_CLOCK_STRING',
        data_type='string',
        virtual=True,
        retrieve_if_name_exists=True,
    )

    t_clock_add_min = client.channels.create(
        name='T_CLOCK_ADD_MIN',
        data_type='int64',
        virtual=True,
        retrieve_if_name_exists=True,
    )

    t_clock_add_sec = client.channels.create(
        name='T_CLOCK_ADD_SEC',
        data_type='int64',
        virtual=True,
        retrieve_if_name_exists=True,
    )

    set_clock_enable = client.channels.create(
        name='SET_T_CLOCK_ENABLE',
        data_type='uint8',
        virtual=True,
        retrieve_if_name_exists=True,
    )

    clock_enable_index = client.channels.create(
        name='T_CLOCK_ENABLE_INDEX',
        is_index=True,
        data_type=sy.DataType.TIMESTAMP,
        retrieve_if_name_exists=True,
    )
    clock_enable = client.channels.create(
        name='T_CLOCK_ENABLE',
        data_type='uint8',
        index=clock_index.key,
        retrieve_if_name_exists=True,
    )

    input_channels = [
        t_clock_add_min.key,
        t_clock_add_sec.key,
        set_clock_enable.key,
    ]

    output_channels = [
        clock.key,
        clock_sec.key,
        clock_min.key,
        clock_string.key,
        clock_index.key,
        clock_enable.key,
        clock_enable_index.key,
    ]

    with client.open_streamer(input_channels) as streamer, \
        client.open_writer(
            start=sy.TimeStamp.now(), 
            channels=output_channels, 
            enable_auto_commit=True
        ) as writer:

        t_clock = sy.TimeSpan.from_seconds(0)
        clock_offset = sy.TimeSpan.from_seconds(0)
        clock_running = False
        start = sy.TimeStamp.now()

        last_minutes = 10000 # arbitrary, higher than starting time
        last_seconds = 10000

        while True:
            frame = streamer.read(5 * sy.TimeSpan.MILLISECOND)
            current_time = sy.TimeStamp.now()

            if frame is not None:
                for v in frame[set_clock_enable.key]:
                    if v == 1:
                        clock_running = True

                        clock_offset = t_clock - current_time.since(start)
                    elif v == 0:
                        clock_running = False

                for v in frame[t_clock_add_sec.key]:
                    clock_offset = clock_offset + v * sy.TimeSpan.SECOND
                    t_clock = clock_offset
                for v in frame[t_clock_add_min.key]:
                    clock_offset = clock_offset + v * sy.TimeSpan.MINUTE
                    t_clock = clock_offset

            if clock_running:
                t_clock = current_time.since(start) + clock_offset

            is_negative = t_clock.milliseconds < 0
            abs_ms = abs(t_clock.milliseconds)

            sign_prefix = '-' if is_negative else ''

            minutes = int(abs_ms // 60000)
            seconds = int((abs_ms // 1000) % 60)
            milliseconds = int(t_clock.milliseconds % 1000)

            if minutes != last_minutes or seconds != last_seconds:

                the_string = f'{sign_prefix}{minutes:d}:{seconds:02d}'

                writer.write({
                    clock_string: the_string,
                })
                last_minutes = minutes
                last_seconds = seconds

            writer.write({
                clock: t_clock.milliseconds,
                clock_sec: seconds,
                clock_min: minutes,
                clock_index: sy.TimeStamp.now(),
                clock_enable: int(clock_running),
                clock_enable_index: sy.TimeStamp.now(),
            })

if __name__ == '__main__':
    main()
