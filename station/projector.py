#!/usr/bin/python3 -su
# /usr/bin/env python3

# -*- coding: utf-8 -*-
# encoding: utf-8
# coding: utf-8

"""
TCP/IP Client to Crestron system's Projector-API.

0. check localhost name (Is it a Station with Projector?)
1. check CLI arguments to determine Target Projectors and client termination condition
2. in a loop probe all possibly open ports on Crestron system and on the first open one do:
   in a loop send requests and parse responses, until termination condition is satisfied

Possible targets:
   one of Projectors or
   all of them

Possible termination conditions:
   ON (resp. OFF) -> wait until _all_ targets are ON (resp. OFF),
   STATUS -> wait for state respone about each target,
   LISTEN -> wait indefinitely.

"""

# TODO: query server for all known hosts/supported commands?
# TODO: quit timeout ???

from __future__ import absolute_import, print_function, unicode_literals

import socket
import io
import re
import sys
import select
import errno
import platform
import os

from time import sleep, time
import datetime

# Comma-separated list of all known hosts with projectors (overrides the list provided by Crestron):
ENV_ALL_PROJECTORS = os.environ.get('ALL_PROJECTORS', None) 

PRJ = [] # Global list of all projector IDs
if ENV_ALL_PROJECTORS:
    PRJ = ENV_ALL_PROJECTORS.split(',')

# Crestron Server Connection details:
CRESTRON_HOST = os.environ.get('CRESTRON_HOST', '172.16.31.13')
CRESTRON_PORT = int(os.environ.get('CRESTRON_PORT', str(3629)))
CRESTRON_PORT_COUNT = int(os.environ.get('CRESTRON_PORT_COUNT', str(8)))

# Maximal number of connection rounds (to each known port)
CONNECTION_TRY_ROUND_COUNT = int(os.environ.get('CONNECTION_TRY_ROUND_COUNT', str(5)))

COMMAND_RETRY_TIMEOUT = int(os.environ.get('CONNECTION_TRY_ROUND_COUNT', str(2*60)))  # in seconds

# possible target states:
OFF = [u'OFF', u'OFF,OFF']
ON = [u'ON',  u'ON,ON']

# request / response separator
EOC = '\x0a'


#################################################################
#isRoot = (os.geteuid() == 0)
def print_timestamp(*args, **kwargs):
    print(datetime.datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S') +":", *args, **kwargs)
#    sys.stdout.flush()
#   if isRoot


#################################################################
STAT = {}  # Global registry with statuses of Projectors


def get_stat(p, default='?'):
    return(STAT.get(p, default))


#################################################################
def send_requests(sock, action, Targets):  # should immediately respond with current status
    message = ''
    for p in Targets:
        message += 'PRJ_' + p + '_PWR_'
        if action in ['ON', 'OFF']:
            message += action
        else:
            assert (action == 'LISTEN') or (action == 'STATUS')
            message += 'STAT=?'
        message += EOC

    print_timestamp('Request: {!r}'.format(message))

    return(sock.sendall(message.encode('utf-8')) is None)  # NOTE: send all requests together..!?


#################################################################
def socket_communicator(sock, timeout, action_request=(lambda s: True), socket_recv_max_size=1024, socket_select_wait=0.5, idle_wait=1.5):  # https://stackoverflow.com/a/8387235
    assert sock

    run_main_loop = action_request(sock)
    t = time()
    sock.setblocking(0)  # NOTE: side-effects are possible!
    while run_main_loop:
        # buffer += sock.recv(1024)  # NOTE: blocking read!
        read_ready, _a, _b = select.select([sock], [], [], socket_select_wait)
        if sock in read_ready:
            # The socket have data ready to be received
            continue_recv = True

            while continue_recv:
                try:
                    # Try to receive some more data & convert to string
                    yield (sock.recv(socket_recv_max_size).decode('utf-8'))

                except socket.error as e:
                    if e.errno != errno.EWOULDBLOCK:
                        # Error! Print it and tell main loop to stop
                        print_timestamp('ERROR: cannot receive data: [%r]. Connection closed by server or network problem?' % e)
                        run_main_loop = False
                    # If e.errno is errno.EWOULDBLOCK, then no more data
                    continue_recv = False

        if time() - t >= timeout:  # timeout for resending original request
            run_main_loop = action_request(sock)
            t = time()
        else:
            sleep(idle_wait)


#################################################################
# Create a TCP/IP socket
def server_connection():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for _i in range(1, CONNECTION_TRY_ROUND_COUNT):  # try a few rounds with some delays
        for _p in range(0, CRESTRON_PORT_COUNT + 1):  # Look for an open port by trying to open all possible ones:
            _port = CRESTRON_PORT + _p
            try:
                sock.connect((CRESTRON_HOST, _port))
            except Exception as _a:
                print_timestamp("WARNING: looks like connection to {}:{} is not possible ({})!".format(CRESTRON_HOST, _port, _a))
                continue

            return sock
        sleep(i*3)

    raise Exception('ERROR: cannot connect to the CrestronSystem (via {}:{}-{})'.format(CRESTRON_HOST, CRESTRON_PORT, CRESTRON_PORT + CRESTRON_PORT_COUNT))
#    return None

##########################################################################################
def main_loop(action, target_spec):
    # binary_stream = io.BytesIO()
    response_regexp = re.compile(r"PRJ_(.*)_STAT=([^=\n]+)$")
    buffer = ''
    ret = 0

    Targets = []

    if target_spec == 'all':
        Targets = PRJ
    elif target_spec in PRJ:
        Targets = [target_spec]
    else:
        print('WARNING: possibly wrong target projector spec: [{}]!'.format(target_spec))
        Targets = [target_spec]

    _sock = None  ## Socket for connection with Crestron server
    try:

        while True:
            while not _sock:
                _sock = server_connection()

            assert _sock

            _empty_buffer = 0
            for b in socket_communicator(_sock, COMMAND_RETRY_TIMEOUT,
                        action_request=(lambda s: send_requests(s, action, Targets))):

                if len(b) == 0:
                    if not _sock:
                        break

                    _empty_buffer += 1
                    if _empty_buffer >= 5:
                        print_timestamp('WARNING: possibly broken connection to Crestron (got {} empty responses)! About to reconnect...'.format(_empty_buffer))
                        if _sock:
                            _sock.close()
                            _sock = None
                        break
                    else:
                        continue
                else:
                    _empty_buffer = 0

                buffer += b
                print_timestamp('Response: {!r} [{}]'.format(buffer, len(buffer)))

                items = buffer.split(EOC)
                for s in items[:-1]:
                    match = response_regexp.match(s)
                    if match:
                        p = match.group(1)  # projector name
                        st = match.group(2)  # new status string
                        curr = get_stat(p)
                        if curr != st:  # NOTE: check goal condition after each state change:
                            print_timestamp('State of \'{}\': {} -> {}'.format(p, curr, st))
                            STAT[p] = st

                            if p in Targets:
                                if action == 'STATUS':
                                    if all(get_stat(t) != '?' for t in Targets):  # any status: ON/OFF/COOLING/WARMING etc...
                                        return ret
                                elif action == 'ON':
                                    if get_stat(p) in ON:
                                        Targets.remove(p)
                                        if not Targets:
                                            return ret
                                elif action == 'OFF':
                                    if get_stat(p) in OFF:
                                        Targets.remove(p)
                                        if not Targets:
                                            return ret
                                # assert (action == 'LISTEN')

                    else:
                        print_timestamp('WARNING: unexpected response: [{}]!'.format(s))

                buffer = items[-1]  # the rest after last EOC separator: ''!
                assert buffer == ''

                if not _sock:
                    break

            sleep(120)

    except Exception as e:
        print_timestamp('ERROR: [{!r}]'.format(e))
        ret = -1
    finally:
        if _sock:
            _sock.close()
            _sock = None
    return ret

##########################################################################################
if __name__ == "__main__":
    _start = time()

    if socket.gethostname().find('.') >= 0:
        name = socket.gethostname()
    else:
        name = socket.gethostbyaddr(socket.gethostname())[0]

    # print("localhost: {}".format(name))
    assert name in [socket.gethostname(), socket.getfqdn(), os.uname()[1], platform.node(), platform.uname()[1]]

    #####################################################################
    _action = 'STATUS'
    if len(sys.argv) >= 2:
        a = str(sys.argv[1]).upper()
        if a in ['ON', 'OFF', 'STATUS', 'LISTEN']:
            _action = a
        else:
            print_timestamp('CLI arguments: [{}].'.format(sys.argv))

            print('ERROR: wrong target state spec: [{}] (should be ON, OFF, STATUS or LISTEN)'.format(_action))
            print('Usage: {} [(STATUS|LISTEN|ON|OFF) [(all|kiosk023(106|143|212).ads.eso.org)]]'.format(sys.argv[0]))
            sys.exit(-1)
        #        print('WARNING: Ignoring wrong target state spec: [{}] (should be ON, OFF, STATUS or LISTEN), Default: [{}]'.format(a, _action))

        if len(sys.argv) >= 3:
            a = str(sys.argv[2]).lower()
            if (a in PRJ) or (a == 'all'):
                name = a
            else:
                print_timestamp('CLI arguments: [{}].'.format(sys.argv))
                print('WARNING: possibly wrong target argument: [{}] (it should be "all" or projector host name!)'.format(a))
                name = a  # 'all'
            #            sys.exit(-1)

            if len(sys.argv) >= 4:
                print('WARNING: Ignoring further present arguments: [{}]'.format(sys.argv[3:]))

        assert _action in ['ON', 'OFF', 'STATUS', 'LISTEN']
    else:
        # No CLI arguments...
        print('Usage: {} [(STATUS|LISTEN|ON|OFF) [(all|kiosk023(106|143|212).ads.eso.org)]]'.format(sys.argv[0]))
        sys.exit(0)

    print_timestamp('Function: [{}], Target projector(s): [{}]'.format(_action, name))
    # print_timestamp()

    try:
        sys.exit(main_loop(_action, name))
    except KeyboardInterrupt:
        e = sys.exc_info()[1]
        sys.stderr.write("\nUser interrupted process.\n")
#        sys.stderr.flush()
        sys.exit(0)
    except SystemExit:
        e = sys.exc_info()[1]
        sys.exit(e.code)
    except Exception:
        e = sys.exc_info()[1]
        sys.stderr.write("\nERROR: unhandled exception occurred: (%s).\n" % e)
#        sys.stderr.flush()
        sys.exit(-1)
    finally:
        if STAT:
            print_timestamp("Final state(s): ", STAT)
        print_timestamp("Time spent: {} sec".format(time() - _start))
