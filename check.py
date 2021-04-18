import click
import json
import re
import subprocess

CONTEXT_SETTINGS = dict(help_option_names=['--help', '-h'])

# For recognizing a "bike request" message.
RE_REQUEST = re.compile(r"""(
                            [
                                \U0001f6b2 # bike emoji
                                \U0001f6b4 # person on bike emoji
                                \U0001f6b5 # person on mountain bike emoji
                            ]
                            .*
                            \U0001f64f     # pray emoji
                        )""", re.VERBOSE)

# For capturing latitude and longitude from a "bike request" message.
RE_LATLON = re.compile(r"""(
                            https://maps\.google\.com/maps\?q=
                            (-?[\d\.]+)    # latitude
                            %2C
                            (-?[\d.]+)     # longitude
                        )""", re.VERBOSE)

@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--bikeshare-user',
              required=True,
              help='Bikeshare Toronto member account username.',
              envvar='2B2S_BIKESHARE_USER',
              )
@click.option('--bikeshare-pass',
              required=True,
              help='Bikeshare Toronto member account password',
              envvar='2B2S_BIKESHARE_PASS',
              )
@click.option('--signal-group', '-c',
              required=True,
              help='Signal messengers group ID',
              envvar='2B2S_SIGNAL_GROUP_ID',
              )
def check_signal_group(bikeshare_user, bikeshare_pass, signal_group):
    """Check messages in a Signal group for Bikeshare Toronto code requests."""

    proc = subprocess.run(
            ["signal-cli", "--output", "json", "receive"],
            stdout=subprocess.PIPE,
            text=True,
            )
    messages_data = json.loads(proc.stdout)
    print(messages_data)
    msg = messages_data['envelope']['syncMessage']['sentMessage']
    print(msg['message'])
    is_group = msg['groupInfo']['groupId'] == signal_group
    if is_group:
        print("Parsing new messages in Signal group...")

        found_request = RE_REQUEST.search(msg['message'])
        if found_request and found_request:
            print("Request detected!")
            found_location = RE_LATLON.search(msg['message'])
            if found_location:
                full, latitude, longitude, *kw = found_location.groups()
                print(latitude)
                print(longitude)

if __name__ == '__main__':
    check_signal_group()
