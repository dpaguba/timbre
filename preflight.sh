#!/usr/bin/env bash
# Shared prerequisite checks for start.sh and dev.sh.
# Sourced, not executed: it defines timbre_preflight and nothing else.
#
# Every check fails with the command to run rather than a raw shell error, so a
# missing tool is a one-line fix instead of a stack trace three steps later.
#
# ffmpeg is deliberately not checked: decoding goes through PyAV, which links
# the ffmpeg libraries itself. Debian and Ubuntu ship the venv bootstrap
# separately, and `ensurepip` rather than `venv` is the piece that is actually
# missing there, so that is what gets probed. An unparsable version fails closed.

timbre_preflight() {
  local need_node="${1:-yes}"


  if ! command -v python3 >/dev/null 2>&1; then
    echo >&2 "python3 was not found. Install Python 3.10 or newer:"
    echo >&2 "    macOS:  brew install python@3.12"
    echo >&2 "    Linux:  sudo apt install python3 python3-venv"
    return 1
  fi

  if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo >&2 "Python 3.10 or newer is required, found $(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')."
    echo >&2 "Install a newer Python and make sure python3 points at it."
    return 1
  fi

  if ! python3 -c 'import ensurepip' >/dev/null 2>&1; then
    echo >&2 "The Python venv module is missing. On Debian or Ubuntu:"
    echo >&2 "    sudo apt install python3-venv"
    return 1
  fi

  if [ "$need_node" = "yes" ]; then
    if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
      echo >&2 "Node.js was not found. Install the LTS release from https://nodejs.org"
      echo >&2 "    macOS:  brew install node"
      echo >&2 "    Linux:  see https://github.com/nodesource/distributions"
      echo >&2 "It is needed to build the frontend."
      return 1
    fi

    local node_major
    node_major="$(node -v | sed 's/^v\([0-9]*\).*/\1/')"
    if ! [[ "$node_major" =~ ^[0-9]+$ ]] || [ "$node_major" -lt 18 ]; then
      echo >&2 "Node.js 18 or newer is required, found $(node -v)."
      return 1
    fi
  fi

  return 0
}
