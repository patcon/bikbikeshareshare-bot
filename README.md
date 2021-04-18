# bike bike share share bot

A bot for watching a Signal messenger group, and sharing bikeshare pin codes for those who ask.

Currently it is preparing to detect shared location pins with variants of ":bike::pray:" in the description.

## To Do

- [x] get signal-cli working
- [x] detect messages
- [x] extract latitude and longitude
- [ ] talk to bikeshare api with auth token
- [ ] find nearest station
- [ ] get ride code
- [ ] do real user/pass auth with bikeshare api
- [ ] figure out dbus messaging bus

## Usage

```
pipenv install
cp sample.env .env
vim .env
pipenv run python check.py
```
