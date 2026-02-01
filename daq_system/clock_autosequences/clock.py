import synnax as sy
from datetime import datetime

client = sy.Synnax(
    host= "192.168.2.59",
    port=9090,
    username='Bill',
    password='Bill',
)

def log_event(message, writer, log_key):
    """Log events with timestamps."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    fullMessage = f"[{timestamp}] {"Clock: "}{message}"
    print(fullMessage)
    writer.write({log_key: [fullMessage]})

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
    clock_s = client.channels.create(
        name='T_CLOCK_S',
        data_type='float64',
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
    hold_state = client.channels.create(
        name='CLOCK_HOLD_STATE',
        data_type='uint8',
        index=clock_index.key,
        retrieve_if_name_exists=True,
    )
    shutdown_channel = client.channels.create(
        name="SEQUENCE_SHUTDOWN",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )
    log_channel = client.channels.create(
        name="BCLS_LOG",
        data_type= 'String',
        virtual=True,
        retrieve_if_name_exists=True,
    )
    
    input_channels = [
        t_clock_add_min.key,
        t_clock_add_sec.key,
        set_clock_enable.key,
        shutdown_channel.key,
    ]

    output_channels = [
        clock.key,
        clock_s.key,
        clock_string.key,
        clock_index.key,
        clock_enable.key,
        hold_state.key,
        clock_enable_index.key,
        log_channel.key,
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

            log_event("Connected to Synnax for trigger monitoring", writer, log_channel.key)
            log_event("Listening for trigger signals", writer, log_channel.key)

            shutdown_flag = False

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
                        seconds = int(t_clock // 60000)
                        clock_offset = clock_offset - seconds + v * sy.TimeSpan.SECOND
                        t_clock = clock_offset
                    for v in frame[t_clock_add_min.key]:
                        mins = int((t_clock // 1000) % 60)
                        clock_offset = clock_offset - mins + v * sy.TimeSpan.MINUTE
                        t_clock = clock_offset
                    for v in frame[shutdown_channel.key]:
                        if v == 1:
                            shutdown_flag = True

                if clock_running:
                    t_clock = current_time.since(start) + clock_offset

                is_negative = t_clock.milliseconds < 0
                abs_ms = abs(t_clock.milliseconds)

                sign_prefix = '-' if is_negative else '+'

                minutes = int(abs_ms // 60000)
                seconds = int((abs_ms // 1000) % 60)

                if not is_negative:
                    seconds += 1

                if minutes != last_minutes or seconds != last_seconds:

                    the_string = f'T{sign_prefix}{minutes:02d}:{seconds:02d}'

                    writer.write({
                        clock_string: the_string,
                    })
                    last_minutes = minutes
                    last_seconds = seconds

                writer.write({
                    clock: t_clock.milliseconds,
                    clock_s: t_clock.milliseconds / 1000.0,
                    clock_index: sy.TimeStamp.now(),
                    clock_enable: int(clock_running),
                    hold_state: int(not clock_running),
                    clock_enable_index: sy.TimeStamp.now(),
                })

                if shutdown_flag:
                    writer.write({
                        clock: 0,
                        clock_s: 0,
                        clock_index: sy.TimeStamp.now(),
                        clock_enable: 0,
                        hold_state: 0,
                        clock_enable_index: sy.TimeStamp.now(),
                    })
                    log_event('Shutting down Clock', writer, log_channel.key)
                    break

if __name__ == '__main__':
    main()
