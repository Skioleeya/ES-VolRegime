#!/usr/bin/env bash
set -euo pipefail

vncserver -kill "${VNC_DISPLAY:-:1}"
