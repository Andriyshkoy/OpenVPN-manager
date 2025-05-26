#!/usr/bin/env bash
# $1 depth  $2 subject
[ "$1" != "0" ] && exit 0
CN=$(echo "$2" | sed -n 's/.*CN=\([^/]*\).*/\1/p')
LIST="/etc/openvpn/server/blocked_clients.txt"
[ -r "$LIST" ] && grep -qx "$CN" "$LIST" && exit 1
exit 0