import click
import json
import re
import subprocess

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

@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--bikeshare-user', '-u',
              required=False,
              help='Bikeshare Toronto member account username.',
              envvar='2B2S_BIKESHARE_USER',
              )
@click.option('--bikeshare-pass', '-p',
              required=False,
              help='Bikeshare Toronto member account password',
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
def check_signal_group(bikeshare_user, bikeshare_pass, bikeshare_auth_token, bikeshare_api_key, signal_group):
    """Check messages in a Signal group for Bikeshare Toronto code requests."""

    proc = subprocess.run(
            ["signal-cli", "--output", "json", "receive"],
            stdout=subprocess.PIPE,
            text=True,
            )
    for line in proc.stdout.strip().split('\n'):
        print(line)
        messages_data = json.loads(line)
        print(messages_data)
        msg = messages_data['envelope']['syncMessage']['sentMessage']
        print(msg['message'])
        is_group = msg['groupInfo']['groupId'] == signal_group
        if is_group:
            print("Parsing new messages in Signal group...")

            found_request = RE_REQUEST.search(msg['message'])
            print(found_request)
            if found_request:
                print("Request detected!")
                found_location = RE_LATLON.search(msg['message'])
                if found_location:
                    full, latitude, longitude, *kw = found_location.groups()
                    print(latitude)
                    print(longitude)

if __name__ == '__main__':
    check_signal_group()
