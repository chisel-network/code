import http.client
import argparse
import json
import ssl
import urllib.parse
import sys
import time
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--session_id', help='Session ID to use for the script', type=str)
parser.add_argument('-p', '--purge', help='Boolean to indicate if all the channels created using the script should be purged', action='store_true')

args = parser.parse_args()
session_id = args.session_id
purge = args.purge

print('Session ID is {}, purge mode: {}'.format(session_id, purge))

headers = {
  'Accept': '*/*',
  'Accept-Language': 'en-US,en;q=0.9',
  'Connection': 'keep-alive',
  'Content-Type': 'application/x-www-form-urlencoded',
  'Cookie': 'applicationStackContainer_selectedChild=configure; session_id={}'.format(session_id),
  'Referer': 'https://127.0.0.1:4433/FSP3000/',
  'Sec-Fetch-Dest': 'empty',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Site': 'same-origin',
  'User-Agent': 'vscode',
  'X-Requested-With': 'XMLHttpRequest',
  'sec-ch-ua': '"Chromium";v="112"',
  'sec-ch-ua-mobile': '?0',
  'sec-ch-ua-platform': '"macOS"'
}

conn_obj = None

def get_connection():
    global conn_obj
    if conn_obj == None:
        conn_obj = http.client.HTTPSConnection("127.0.0.1", 4433, context=ssl._create_unverified_context())
    return conn_obj

def get_all_channels():
    conn = get_connection()
    conn.request("GET", "/FSP3000/scripts/addresses_config?aidGroup=AIDNAME_VCH&entityState=AS_OR_EQ&portSide=&originAddress=OM-1-9-N&relation=descendant-via-children", '', headers)
    res = conn.getresponse()
    data = res.read()
    # conn.close()
    return json.loads(data.decode('utf-8'))['addresses']

def refresh_session_key():
    conn = get_connection()
    conn.request("GET", "/FSP3000/scripts/session_refresh", '', headers)
    res = conn.getresponse()
    data = res.read()
    # conn.close()
    print("Refreshed session : {}".format(data.decode('utf-8')))

def create_channel(name, channel):
    conn = get_connection()
    params = {'_NE;FROM-AID': 'OM-1-9-N', '_NE;CONN': 'BI', '_NE;CONFIG__CRS': 'ADD-DROP', '_NE;EP_CRS_TO_AID_LIST': 'OM-1-9-C2', '_NE;CHANNEL__PROVISION': channel, '_NE;CHAN-BW': '50G', '_NE;TYPE__FACILITY': 'OPTICAL', '_NE;OPTSET-DEV': '0', '_NE;PATH-NODE': '1', '_NE;PATH-NODE__REVERSE': '1', '_NE;ALIAS': name}

    payload = urllib.parse.urlencode(params)

    conn.request("POST", "/FSP3000/scripts/ease_of_use_crs_create_config", payload, headers)
    res = conn.getresponse()
    data = res.read()
    # conn.close()
    print(data.decode("utf-8"))

def get_from_channel_part(channel_id):
    print('getting channel ID from info: {}'.format(channel_id))
    conn = get_connection()
    conn.request("GET", "/FSP3000/scripts/addresses_config?aidGroup=AIDNAME_CRS_CH&entityState=AS_OR_EQ&portSide=&originAddress={}&relation=cross-connection-from".format(channel_id), '', headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))
    data = json.loads(data.decode("utf-8"))
    return data['addresses'][0]

def get_to_channel_part(channel_id):
    conn = get_connection()
    conn.request("GET", "/FSP3000/scripts/addresses_config?aidGroup=AIDNAME_CRS_CH&entityState=AS_OR_EQ&portSide=&originAddress={}&relation=cross-connection-to".format(channel_id), '', headers)
    res = conn.getresponse()
    data = res.read()
    data = json.loads(data.decode('utf-8'))
    return data['addresses'][0]

def enable_service(link):
    conn = get_connection()
    params = {'_{};ADMIN'.format(link): 'IS'}
    payload = urllib.parse.urlencode(params)
    conn.request("POST", "/FSP3000/scripts/system_edit_config", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))

def get_provision_options():
    conn = get_connection()
    conn.request("GET", "/FSP3000/scripts/ease_of_use_crs_create_config?_NE%3BFROM-AID=OM-1-9-N&_NE%3BCONN=BI&_NE%3BCONFIG__CRS=ADD-DROP&_NE%3BEP_CRS_TO_AID_LIST=OM-1-9-C2&_NE%3BCHANNEL__PROVISION=19420", '', headers)
    res = conn.getresponse()
    data = res.read()
    # conn.close()
    json_data = json.loads(data.decode('utf-8'))
    return json_data['parameters'][0]['options']

def get_equalizer_ids():
    conn = get_connection()
    conn.request("GET", "/FSP3000/scripts/addresses_maintenance?aidGroup=AIDNAME_VCH&entityState=AS&portSide=N%2CNx&originAddress=MOD-1-9", '', headers)
    res = conn.getresponse()
    data = res.read()
    json_data = json.loads(data.decode('utf-8'))
    return json_data['addresses']

def equalize(equalizer_channel_id):
    payload = {f'_{equalizer_channel_id};EP_EQLZ_OPR_AND_CONDITION': 'OPR'}
    payload = urllib.parse.urlencode(payload)
    conn = get_connection()
    conn.request("POST", "/FSP3000/scripts/system_edit_maintenance", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))

def get_time_in_milliseconds():
  return round(time.time() * 1000)

def purge_channels():
    all_channels = get_all_channels()
    save_channels = ['VCH-1-9-N-19283', 'VCH-1-9-N-19400', 'VCH-1-9-N-19595']
    for channel in all_channels:
        if channel in save_channels:
            print('Saving: {}'.format(channel))
            continue

        print('Deleting: {}'.format(channel))
        conn = get_connection()
        conn.request("GET", "/FSP3000/scripts/system_delete_config?address={}&force".format(channel), '', headers)
        res = conn.getresponse()
        data = res.read()
        print('Deleted: {} / response {}'.format(channel, data.decode("utf-8")))

def get_equalization_status(channel):
    conn = get_connection()
    conn.request("GET", f"/FSP3000/scripts/system_read_monitor?_{channel};EP_OPT", '', headers)
    res = conn.getresponse()
    data = res.read()
    json_data = json.loads(data.decode('utf-8'))
    print(json_data)
    parameters = json_data['parameters'][0]
    assert(parameters['address'] == channel)
    if 'value' not in parameters:
        return -17
    power_val = parameters['value']
    power_val = str(power_val).replace('&#x2d;', '-').replace('&#x2e;', '.')
    power_val = float(power_val)
    return power_val


def wait_for_equlization(channel):
    while True:
        power_val = get_equalization_status(channel)
        if power_val > -16.4:
            print('Power was {} for channel {}, hence breaking'.format(power_val, channel))
            break
        else:
            print('Power was {} for channel {}, hence waiting'.format(power_val, channel))
        time.sleep(1)

refresh_session_key()

if purge:
    print('Purging channels')
    purge_channels()
    sys.exit(1)

added = 0
while True:
    available_channels = get_provision_options()
    if len(available_channels) == 0:
        break

    available_channel = available_channels[0]
    print('Going to create test channel on: {}/{}'.format(available_channel, len(available_channels)))

    # loop over all the channels, TODO:

    start_time = get_time_in_milliseconds()

    # create channel
    create_channel('python_script_{}'.format(available_channel), available_channel)

    created_channel_id = None
    # Verify it is created
    created_channels = get_all_channels()
    for created_channel in created_channels:
        print('Checking: {}'.format(created_channel))
        if available_channel in created_channel:
            print('FOUND')
            created_channel_id = created_channel
            break

    if created_channel_id == None:
        print('Channel creation has failed us, bye :D')
        sys.exit(1)

    # Get from 
    from_channel = get_from_channel_part(created_channel_id)
    print('From channel is: {}'.format(from_channel))
    # Get to
    to_channel = get_to_channel_part(created_channel_id)
    print('To channel: {}'.format(to_channel))

    print('Waiting before enabling services')

    # enable service for both
    enable_service(from_channel)
    enable_service(to_channel)

    # Get the corresponding ID of this channel required to equalize
    equalizer_ids = get_equalizer_ids()
    for equalizer_id in equalizer_ids:
        if available_channel in equalizer_id:
            print('Found equalizer ID: {} for channel: {}'.format(equalizer_id, available_channel))
            equalize(equalizer_id)
            wait_for_equlization(equalizer_id)

    end_time = get_time_in_milliseconds()

    dt_obj = datetime.utcnow() # get the current UTC datetime object
    millisec = dt_obj.timestamp() * 1000 # convert it to milliseconds
    print(f'LOG,{millisec},{created_channel_id},{end_time - start_time}')

    added += 1
    if added % 30 == 0:
        refresh_session_key()