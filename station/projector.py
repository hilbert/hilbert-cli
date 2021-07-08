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
def send_request_prj_list(sock):  # should immediately respond with current list of targets
    """Query for all known projectors"""
    message = 'PRJ_LIST=?' + EOC
    print_timestamp('Request: {!r}'.format(message))
    return(sock.sendall(message.encode('utf-8')) is None)


#################################################################
def send_requests(sock, action, Targets):  # should immediately respond with current status
    """Query or control projectors"""
    if not Targets:
        print_timestamp('No known handle-targets yet...')
        return(True)

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
def socket_communicator(sock, action_retry_timeout, action_request=(lambda s: True), socket_recv_max_size=1024, socket_select_wait=0.5, idle_wait=1.5, read_timeout = None):  # https://stackoverflow.com/a/8387235
    if not sock:
        return # nothing to read!

    assert sock

    run_main_loop = action_request(sock)
    t = time()
    read_time = time()
    sock.setblocking(0)  # NOTE: side-effects are possible!
    _empty_buffer = 0
    while run_main_loop and sock:
        # buffer += sock.recv(1024)  # NOTE: blocking read!
        read_ready, _a, _b = select.select([sock], [], [], socket_select_wait)
        if sock in read_ready:
            # The socket have data ready to be received
            continue_recv = True

            while continue_recv and sock:
                try:
                    # Try to receive some more data & convert to string
                    b = sock.recv(socket_recv_max_size)
                    read_time = time()

                    if len(b) == 0:
                        _empty_buffer += 1

                        if _empty_buffer >= 50:
                            print_timestamp('WARNING: possibly broken connection to Crestron (got {} empty responses)! Will try to reconnect...'.format(_empty_buffer))
                            continue_recv = False
                            run_main_loop = False
                    else:
                        _empty_buffer = 0

                    yield (b.decode('utf-8'))

                except socket.error as e:
                    if e.errno != errno.EWOULDBLOCK:
                        # Error! Print it and tell main loop to stop
                        print_timestamp('ERROR: cannot receive data: [%r]. Connection closed by server or network problem?' % e)
                        run_main_loop = False
                    # If e.errno is errno.EWOULDBLOCK, then no more data
                    continue_recv = False

                except BrokenPipeError as e:
                    print_timestamp('ERROR: BrokenPipeError caught [{!r}]'.format(e))
                    run_main_loop = False
                    continue_recv = False

        if (not run_main_loop) or (not sock):
            break

        if read_timeout is not None:
            if time() - read_time >= read_timeout:
                run_main_loop = False  # stop waiting to read from network

        if time() - t >= action_retry_timeout:  # timeout for resending original request
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
        sleep(_i*3)

    raise Exception('Cannot connect to the CrestronSystem (via {}:{}-{})'.format(CRESTRON_HOST, CRESTRON_PORT, CRESTRON_PORT + CRESTRON_PORT_COUNT))
#    return None


##########################################################################################
def main_loop(action, target_spec):
    global PRJ
    # binary_stream = io.BytesIO()

    # all possible Crestron responses:
    response_regexp = re.compile(r"PRJ_(.*)_STAT=([^=\n]+)$")
    list_response_regexp = re.compile(r"PRJ_LIST=(.*)$")
    error_response_regexp = re.compile(r"PROTOCOL_ERROR: (.*)$")

    ret = 0

    _sock = None  ## Socket for connection with Crestron server
    _new_list = False
    buffer = ''

    try:
        todos = ''

        # initial stage:
        while True and (not PRJ):
            while not _sock:
                _sock = server_connection()

            assert _sock

            # if we need to know all projectors (and they were not specified from outside) then query them!
            for b in socket_communicator(_sock, COMMAND_RETRY_TIMEOUT,
                action_request=(lambda s: send_request_prj_list(s)), 
                read_timeout = 4*60):

                buffer += b
                items = buffer.split(EOC)

                buffer = ''

                for s in items[:-1]:
                    print_timestamp('Response: [{!r}].'.format(s))

                    # PRJ_LIST=*,*,*
                    match = list_response_regexp.match(s)
                    if match:
                        p = match.group(1)  # CSV list of projectors
                        print_timestamp('List of all known projectors: [{}]'.format(p))

                        # NOTE: Update the list of all projectors only if it was not set via ENV!
                        PRJ = p.split(',')
                        continue

                    # else: keep unprocessed responses for later processing
                    todos += s + EOC

                buffer = items[-1]  # the rest after last EOC separator: ''!

                if buffer != '':
                    print_timestamp('WARNING: possibly missing End-of-response-separator. Tailing buffer: [{!r}]'.format(buffer))

                if PRJ: # stop reading if we already to PRJ_LIST=....!
                    break

        buffer = todos + buffer # NOTE: unhandled respones - may go missing if nothing will be read from the socket :-(

        Targets = []

        if PRJ and (target_spec == 'all'):
            for h in PRJ:
                if h not in Targets:
                    Targets.append(h)
        elif PRJ and (target_spec in PRJ) and (target_spec not in Targets):
            Targets.append(target_spec)
        elif (target_spec != 'all'):
            print('WARNING: possibly wrong target projector spec: [{}]!'.format(target_spec))
            Targets.append(target_spec)

        print_timestamp('Current targets for handling: {}'.format(Targets))

        # main stage
        while True:

            while not _sock:
                _sock = server_connection()

            assert _sock

            for b in socket_communicator(_sock, COMMAND_RETRY_TIMEOUT,
                        action_request=(lambda s: send_requests(s, action, Targets))):

                buffer += b

                items = buffer.split(EOC)
                for s in items[:-1]:
                    print_timestamp('Response: [{!r}]. Processing...'.format(s))

                    # PRJ_*_STAT=*
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
                        continue


                    # PRJ_LIST=*,*,*
                    match = list_response_regexp.match(s)
                    if match:
                        print_timestamp('WARNING: projector list update is not expected on this stage!')

                        p = match.group(1)  # CSV list of projectors
                        print_timestamp('Updated list of projectors: [{}]'.format(p))

                        if not PRJ:  # NOTE: Update the list of all projectors only if it was not set via ENV!
                            PRJ = p.split(',')

                            if target_spec == 'all':
                                for h in PRJ:
                                    if h not in Targets:
                                        print_timestamp('New projector ID: [{}]'.format(h))
                                        Targets.append(h)
                                        # trigger general status update
                                        _new_list = True

                        continue

                    # PROTOCOL_ERROR: ...
                    match = error_response_regexp.match(s)
                    if match: # TODO: the following is untested since it is not yet implemented on the server
                        p = match.group(1)  # error message
                        print_timestamp('WARNING: server could not handle some of our requests: [{}]! Please check projector IDs!'.format(p))
                        continue

                    # else
                    print_timestamp('WARNING: unexpected response: [{}]!'.format(s))

                buffer = items[-1]  # the rest after last EOC separator: ''!

                if buffer != '':
                    print_timestamp('WARNING: possibly missing End-of-response-separator. Tailing buffer: [{!r}]'.format(buffer))

                if _new_list:
                    send_requests(_sock, action, Targets)
                    _new_list = False


            sleep(10)

    except BrokenPipeError as e:
        print_timestamp('ERROR: BrokenPipeError caught [{!r}]'.format(e))
        ret = -1
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
            a = str(sys.argv[2])
            if a.lower() == 'all':
                a = 'all'

            if (a == 'all') or (PRJ and (a in PRJ)):
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
