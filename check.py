import click
import json
import re
import requests
import subprocess
import sys
import textwrap

from math import cos, sqrt

def emojify_bike_code(code):
    code = code.replace('1', "\N{DIGIT ONE}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}") # digit keycap plus empty key
    code = code.replace('2', "\N{DIGIT TWO}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}")
    code = code.replace('3', "\N{DIGIT THREE}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}")
    return code

def generate_station_map_link(lat, lon):
    template = """\
            \N{Bicyclist} \N{Dash Symbol} \N{Round Pushpin} \N{Pedestrian} \N{Pedestrian} \N{Pedestrian} \N{Hourglass with Flowing Sand} \N{Raised Hand with Fingers Splayed}
            https://maps.google.com/maps?q={}%2C{}"""
    template = textwrap.dedent(template)
    return template.format(lat, lon)

CONTEXT_SETTINGS = dict(help_option_names=['--help', '-h'])

# For recognizing a "bike request" message, regardless of skin-tone or gender.
RE_REQUEST = re.compile(re.sub(r'\n +', '', r"""
                            [
                                \N{BICYCLE}
                                \N{BICYCLIST}
                                \N{MOUNTAIN BICYCLIST}
                            ]
                            [\N{Emoji Modifier Fitzpatrick Type-1-2}-\N{Emoji Modifier Fitzpatrick Type-6}]?
                            (\N{Zero Width Joiner}[\N{Female Sign}\N{Male Sign}\N{Male and Female Sign}]\N{Variation Selector-16})?
                            \s*
                            \N{PERSON WITH FOLDED HANDS}
                        """), re.VERBOSE)

# For capturing latitude and longitude from a "bike request" message.
RE_LATLON = re.compile(r"""(
                            https://maps\.google\.com/maps\?q=
                            (-?[\d\.]+)    # latitude
                            %2C
                            (-?[\d.]+)     # longitude
                        )""", re.VERBOSE)

class SignalClient:
    def __init__(self):
        pass

    def fetchMessagesCli(self):
        proc = subprocess.run(
                ["signal-cli", "--output", "json", "receive"],
                stdout=subprocess.PIPE,
                text=True,
                )
        messages = proc.stdout.strip().split('\n')
        messages = [m for m in messages if m != '']
        return messages

    def sendMessageCli(self, group_id, text):
        proc = subprocess.run(
                ["signal-cli", "send", "--group", group_id, "--message", text],
                stdout=subprocess.PIPE,
                text=True,
                )
        return proc.stdout.strip()

    def watchMessagesDbus(self):
        pass

class BikeshareClient():
    ALL_STATIONS = json.loads(open("station_information.json").read())['data']['stations']
    R = 6371000 # radius of the Earth in m
    BASE_URL = 'https://tor.publicbikesystem.net'

    stackify_uuid = '0abd9999-d354-425d-000a-7a0338134d3b'
    debug = False
    noop = True

    def __init__(self, bikeshare_api_key, bikeshare_auth_token):
        self.api_key = bikeshare_api_key
        self.auth_token = bikeshare_auth_token

    def getNearestStations(self, latitude, longitude):
        nearsort = lambda d: self.__distance(d['lon'], d['lat'], longitude, latitude)
        return sorted(self.ALL_STATIONS, key=nearsort)

    def getNearestStation(self, latitude, longitude):
        station = self.getNearestStations(latitude, longitude)[0]
        if self.debug: print(station)
        return station

    def getRideCode(self, station_id, latitude, longitude):
        if self.noop: return '12321'

        uri_path = '/customer/v3/stations/{}/geofence-ride-codes'
        full_url = self.BASE_URL + uri_path.format(station_id)

        payload = {
                'count': 1,
                'latitude': latitude,
                'longitude': longitude,
                }

        headers = {
                'cookie': '.Stackify.Rum={}'.format(self.stackify_uuid),
                'user-agent': 'okhttp/3.12.1',
                'accept-encoding': 'gzip',
                'x-api-key': self.api_key,
                'x-auth-token': self.auth_token,
                }

        if self.debug:
            print(headers)
            print(payload)
            print(full_url)

        r = requests.post(full_url, json=payload, headers=headers)
        res = r.json()

        if self.debug: print(res)

        code = res['codes'][0]['code']

        return code

    # Source: https://stackoverflow.com/a/46641933/504018
    def __distance(self, lon1, lat1, lon2, lat2):
        x = (float(lon2)-float(lon1)) * cos(0.5*(float(lat2)+float(lat1)))
        y = (float(lat2)-float(lat1))
        return self.R * sqrt( x*x + y*y )

@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--bikeshare-user', '-u',
              required=False,
              help='Bikeshare Toronto member account username (not yet functional)',
              envvar='2B2S_BIKESHARE_USER',
              )
@click.option('--bikeshare-pass', '-p',
              required=False,
              help='Bikeshare Toronto member account password (not yet functional)',
              envvar='2B2S_BIKESHARE_PASS',
              )
@click.option('--bikeshare-auth-token', '-t',
              required=True,
              help='Bikeshare Toronto member account derived authorization token',
              envvar='2B2S_BIKESHARE_AUTH_TOKEN',
              )
@click.option('--bikeshare-api-key', '-k',
              required=True,
              default='b71d6720c8f211e7b7ee0a3571039f73',
              help='Bikeshare Toronto application API key',
              envvar='2B2S_BIKESHARE_API_KEY',
              )
@click.option('--signal-group', '-g',
              required=True,
              help='Signal messengers group ID',
              envvar='2B2S_SIGNAL_GROUP_ID',
              )
@click.option('--noop',
              is_flag=True,
              help='Fake contact to Bikeshare servers',
              )
@click.option('--debug', '-d',
              is_flag=True,
              help='Show debug output',
              )
def check_signal_group(bikeshare_user, bikeshare_pass, bikeshare_auth_token, bikeshare_api_key, signal_group, noop, debug):
    """Check messages in a Signal group for Bikeshare Toronto code requests."""

    signal = SignalClient()

    bikeshare = BikeshareClient(bikeshare_api_key, bikeshare_auth_token)
    bikeshare.noop = noop
    bikeshare.debug = debug

    messages = signal.fetchMessagesCli()
    for line in messages:
        messages_data = json.loads(line)
        if debug: print(messages_data)

        def get_message(data):
            sync_message = data['envelope'].get('syncMessage', None)
            if sync_message:
                sent_message = sync_message.get('sentMessage', None)
                return sent_message

            return None

        msg = get_message(messages_data)

        if msg:
            if debug: print(msg['message'])
            group = msg.get('groupInfo', None)
            if group and group['groupId'] == signal_group:
                print("Parsing new messages in Signal group...")

                found_request = RE_REQUEST.search(msg['message'])
                if debug: print(found_request)
                if found_request:
                    print("Request detected!")
                    found_location = RE_LATLON.search(msg['message'])
                    if found_location:
                        full, latitude, longitude, *kw = found_location.groups()
                        if debug:
                            print(latitude)
                            print(longitude)

                        print('Fetching nearest station...')
                        station = bikeshare.getNearestStation(latitude, longitude)

                        # Replace dropped pin latlon with station latlon.
                        # TODO: Randomize these a bit.
                        latitude = station['lat']
                        longitude = station['lon']
                        code = bikeshare.getRideCode(station['station_id'], latitude, longitude)

                        code_msg = "\N{Sparkles} " + emojify_bike_code(code)
                        station_map_msg = generate_station_map_link(latitude, longitude)

                        if debug:
                            print(code_msg)
                            print(station_map_msg)

                        signal.sendMessageCli(signal_group, code_msg)
                        signal.sendMessageCli(signal_group, station_map_msg)

if __name__ == '__main__':
    check_signal_group()
