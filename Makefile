PHONE = +13475597622

start-daemon:
	signal-cli --output=json --username="${PHONE}" daemon
