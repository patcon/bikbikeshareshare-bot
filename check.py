import click
import json
import re
import subprocess

CONTEXT_SETTINGS = dict(help_option_names=['--help', '-h'])

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
    message = messages_data['envelope']['syncMessage']['sentMessage']['message']
    print(message)
    # One of the three bike emoji plus a pray emoji, with space for extra skin tone code points.
    RE_REQUEST = re.compile(r"""
                                [
                                    \U0001f6b2 # bike emoji
                                    \U0001f6b4 # person on bike emoji
                                    \U0001f6b5 # person on mountain bike emoji
                                ]
                                .*
                                \U0001f64f     # pray emoji
                            """, re.VERBOSE)
    RE_LATLON = re.compile(r"""
                                https://maps\.google\.com/maps\?q=
                                (-?[\d\.]+)    # latitude
                                %2C
                                (-?[\d.]+)     # longitude
                            """, re.VERBOSE)
    found_request = RE_REQUEST.search(message)
    if found_request:
        print("Request detected!")
        match = RE_LATLON.search(message)
        lat = match.group(1)
        lon = match.group(2)
        print(lat)
        print(lon)

if __name__ == '__main__':
    check_signal_group()
