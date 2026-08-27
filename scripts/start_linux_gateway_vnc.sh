#!/usr/bin/env bash
set -euo pipefail

display="${VNC_DISPLAY:-:2}"
geometry="${VNC_GEOMETRY:-1440x900}"

vncserver "$display" -geometry "$geometry" -localhost yes
DISPLAY="$display" LIBGL_ALWAYS_SOFTWARE=1 nohup "$HOME/Jts/ibgateway" \
  >/tmp/ibgateway-linux.log 2>&1 </dev/null &

printf 'VNC display: %s\n' "$display"
printf 'VNC port: 590%s\n' "${display#:}"
printf 'Gateway log: /tmp/ibgateway-linux.log\n'
printf 'Connect locally with a VNC viewer, then log in to Paper Account.\n'
