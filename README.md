# bike bike share share bot

A bot for watching a Signal messenger group, and sharing bikeshare pin codes for those who ask.

Currently it is preparing to detect shared location pins with variants of ":bike::pray:" in the description.

## To Do

- [x] get signal-cli working
- [x] detect messages
- [x] extract latitude and longitude
- [ ] auth with bikeshare api
- [ ] find nearest station
- [ ] get ride code

## Usage

```
pipenv install
cp sample.env .env
vim .env
pipenv run python check.py
```
