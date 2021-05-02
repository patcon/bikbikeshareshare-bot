PHONE = +17787662227

start-daemon:
	signal-cli --output=json --username="${PHONE}" daemon

prepare-osx:
	export DBUS_SESSION_BUS_ADDRESS=unix:path=$$DBUS_LAUNCHD_SESSION_BUS_SOCKET
