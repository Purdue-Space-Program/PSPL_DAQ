from enum import IntEnum
from struct import calcsize, pack, unpack
from socket import socket, AF_INET, SOCK_STREAM
from typing import Any
import constants
import utils

telem_df   = utils.get_telem_configs()
command_df = utils.get_command_configs()

class Command(IntEnum):
    SET_FU_UPPER_SETP = 0
    SET_FU_LOWER_SETP = 1
    SET_OX_UPPER_SETP = 2
    SET_OX_LOWER_SETP = 3
    SET_FU_STATE_REGULATE = 4
    SET_FU_STATE_ISOLATE  = 5
    SET_FU_STATE_OPEN     = 6
    SET_OX_STATE_REGULATE = 7
    SET_OX_STATE_ISOLATE  = 8
    SET_OX_STATE_OPEN     = 9
    SET_BB_STATE_REGULATE = 10
    SET_BB_STATE_ISOLATE  = 11
    SET_BB_STATE_OPEN     = 12
    NOOP  = 13
    START = 14
    ABORT = 15
    SET_FU_UPPER_REDLINE = 16
    SET_FU_LOWER_REDLINE = 17
    SET_OX_UPPER_REDLINE = 18
    SET_OX_LOWER_REDLINE = 19
    REDLINE_RESET = 25

class Status(IntEnum):
    SUCCESS = 0
    NOT_ENOUGH_ARGS = 1
    TOO_MANY_ARGS   = 2
    UNRECOGNIZED_COMMAND = 3

aliases = {
    Command.SET_FU_STATE_REGULATE: ('bb_fu_reg', 'bb_fu_regulate'),
    Command.SET_FU_STATE_ISOLATE:  ('bb_fu_iso', 'bb_fu_isolate'),
    Command.SET_FU_STATE_OPEN:      'bb_fu_open',
    Command.SET_OX_STATE_REGULATE: ('bb_ox_reg', 'bb_ox_regulate'),
    Command.SET_OX_STATE_ISOLATE:  ('bb_ox_iso', 'bb_ox_isolate'),
    Command.SET_OX_STATE_OPEN:      'bb_ox_open',
    Command.SET_FU_UPPER_SETP:      'fu_set_upper',
    Command.SET_FU_LOWER_SETP:      'fu_set_lower',
    Command.SET_OX_UPPER_SETP:      'ox_set_upper',
    Command.SET_OX_LOWER_SETP:      'ox_set_lower',
}

commands = dict()

for _, row in command_df.iterrows():
    name = str(row['Name']).lower()
    id   = row['ID']

    commands[name] = id

for cmd, alias in aliases.items():
    if isinstance(alias, tuple):
        for a in alias:
            commands[a] = int(cmd)
    else:
        commands[alias] = int(cmd)

def print_help() -> None:
    print('Help!')

def send_command(cmd: str, args: list[Any] | None = None, sock = None) -> Status:
    cmd   = cmd.lower()
    fargs = [float(a) for a in args] if args else []

    cmd_id = commands[cmd]
    c_row  = command_df[command_df['ID'] == cmd_id].squeeze()

    match Command(cmd_id):
        case Command.SET_FU_UPPER_SETP     \
            | Command.SET_FU_LOWER_SETP    \
            | Command.SET_FU_UPPER_REDLINE \
            | Command.SET_FU_LOWER_REDLINE:

            cmd_row = telem_df[telem_df['Name'] == 'PT-FU-201'].squeeze()
            if args:
                fargs = [int(((((i - cmd_row['Zeroing Offset']) - cmd_row['Offset']) / cmd_row['Slope']) - constants.ADC_V_OFFSET) / float(constants.ADC_V_SLOPE)) for i in fargs]

        case Command.SET_OX_UPPER_SETP     \
            | Command.SET_OX_LOWER_SETP    \
            | Command.SET_OX_UPPER_REDLINE \
            | Command.SET_OX_LOWER_REDLINE:

            cmd_row = telem_df[telem_df['Name'] == 'PT-OX-201'].squeeze()
            if args:
                fargs = [int(((((i - cmd_row['Zeroing Offset']) - cmd_row['Offset']) / cmd_row['Slope']) - constants.ADC_V_OFFSET) / float(constants.ADC_V_SLOPE)) for i in fargs]

    packet = pack('<B' + ('Q' * c_row['Num Args']), cmd_id, *fargs)
    if sock:
        sock.send(packet)
        ret = sock.recv(1)
    else:
        with socket(AF_INET, SOCK_STREAM) as s:
            s.connect((constants.AVI_IP, constants.AVI_CMD_PORT))
            s.send(packet)
            ret = s.recv(1)
    return Status(int.from_bytes(ret, byteorder='big'))

if __name__ == '__main__':
    try:
        while True:
            inp = input('> ').lower().strip(' \n').split(' ')

            if inp[0] == 'help' or inp[0] == 'h':
                print_help()
                continue

            if inp[0] in commands:
                print(f'Status: {send_command(inp[0], inp[1:]).name}')
            elif inp[0] != '':
                print('Command not recognized!!')

    except KeyboardInterrupt:
        print()
        pass
