import base64
import click
import json
import re
import requests
import subprocess
import sys
import textwrap

from datetime import datetime
from gi.repository import GLib
from math import cos, sqrt
from pydbus import SessionBus
from random import randrange

def emojify_numbers(code):
    code = code.replace('1', "\N{DIGIT ONE}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}")
    code = code.replace('2', "\N{DIGIT TWO}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}")
    code = code.replace('3', "\N{DIGIT THREE}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}")
    code = code.replace('4', "\N{DIGIT FOUR}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}")
    code = code.replace('5', "\N{DIGIT FIVE}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}")
    code = code.replace('6', "\N{DIGIT SIX}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}")
    code = code.replace('7', "\N{DIGIT SEVEN}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}")
    code = code.replace('8', "\N{DIGIT EIGHT}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}")
    code = code.replace('9', "\N{DIGIT NINE}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}")
    code = code.replace('0', "\N{DIGIT ZERO}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}")
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

RE_CHECKIN = re.compile(r"\U0001F512\u2B05\uFE0F\U0001F6B2")

# For capturing latitude and longitude from a "bike request" message.
RE_LATLON = re.compile(r"""(
                            https://maps\.google\.com/maps\?q=
                            (-?[\d\.]+)    # latitude
                            %2C
                            (-?[\d.]+)     # longitude
                        )""", re.VERBOSE)

class SignalClient:
    debug = False

    def __init__(self):
        pass

    def fetchAllMessagesCli(self):
        proc = subprocess.run(
                ["signal-cli", "--output", "json", "receive"],
                stdout=subprocess.PIPE,
                text=True,
                )
        messages = proc.stdout.strip().split('\n')
        messages = [json.loads(m) for m in messages if m != '']
        if self.debug: [print(m) for m in messages]
        return messages

    def fetchSyncMessagesCli(self, group_id):
        def get_message(data):
            sync_message = data['envelope'].get('syncMessage', None)
            if sync_message:
                sent_message = sync_message.get('sentMessage', None)
                return sent_message

            return None

        messages = [get_message(m) for m in self.fetchAllMessagesCli() if get_message(m)]
        if group_id:
            messages = [m for m in messages if m.get('groupInfo', {}).get('groupId', None) == group_id]
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

    def getLastTrip(self):
        if self.noop: return (bool(randrange(2)), (30*60) - 5 + randrange(10))

        uri_path = '/customer/v3/profile/trips?open=false'
        full_url = self.BASE_URL + uri_path

        headers = {
                'cookie': '.Stackify.Rum={}'.format(self.stackify_uuid),
                'user-agent': 'okhttp/3.12.1',
                'accept-encoding': 'gzip',
                'x-api-key': self.api_key,
                'x-auth-token': self.auth_token,
                }

        r = requests.get(full_url, headers=headers)
        res = r.json()

        if self.debug: print(res)

        last_trip = res['trips'].pop()
        start = datetime.fromisoformat(last_trip['startTime'].replace('Z', ''))
        end = datetime.fromisoformat(last_trip['endTime'].replace('Z', ''))
        delta = end - start

        return (last_trip['open'], delta.seconds)

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

    bikeshare = BikeshareClient(bikeshare_api_key, bikeshare_auth_token)
    bikeshare.noop = noop
    bikeshare.debug = debug

    def byteArray2string(byteArray):
        byteString = bytes(byteArray)
        string = base64.b64encode(byteString)
        # Convert byte string to unicode string
        string = string.decode()
        return string

    def string2byteArray(string):
        return list(base64.b64decode(string))

    def processMessage(timestamp, source, dest, groupIdBytes, message, attachments):
        group_id = byteArray2string(groupIdBytes)
        if signal_group != group_id: return

        group_name = signal.getGroupName(groupIdBytes)

        print("Parsing new messages in Signal group...")

        found_request = RE_REQUEST.search(message)
        if debug: print(found_request)

        found_checkin = RE_CHECKIN.search(message)
        if debug: print(found_checkin)

        if found_checkin:
            print("Checkin detected!")
            is_open, total_seconds = bikeshare.getLastTrip()
            minutes = (total_seconds//60) % 60
            seconds = total_seconds - minutes*60
            duration = "{} {}".format(str(minutes), str(seconds).zfill(2))
            hourglass = "\N{Grimacing Face}\N{Hourglass with Flowing Sand}" if is_open else "\N{Hourglass}"
            duration_msg = hourglass + " " + emojify_numbers(duration)

            signal.sendGroupMessage(duration_msg, None, string2byteArray(signal_group))

        elif found_request:
            print("Request detected!")
            found_location = RE_LATLON.search(message)
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

                code_msg = "\N{Sparkles} " + emojify_numbers(code)
                station_map_msg = generate_station_map_link(latitude, longitude)

                if debug:
                    print(code_msg)
                    print(station_map_msg)

                signal.sendGroupMessage(code_msg, None, string2byteArray(signal_group))
                signal.sendGroupMessage(station_map_msg, None, string2byteArray(signal_group))

    bus = SessionBus()
    loop = GLib.MainLoop()

    signal = bus.get('org.asamk.Signal')

    signal.onSyncMessageReceived = processMessage
    signal.onMessageReceived = processMessage
    loop.run()

if __name__ == '__main__':
    check_signal_group()
