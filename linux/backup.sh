#! /bin/bash
set -o nounset
set -o errexit

# Get the directory of current shell, so we can calculate the "PortableTrac" path in git repo.
if [ -z $BASH ]; then
    echo "This shell script MUST run under bash."
    exit /b -1
fi
_script="$(readlink -f "${BASH_SOURCE[0]}")"
_script_dir="$(dirname "$_script")"
echo "Directory of $_script : $_script_dir"

# Define SITE_BASE
if [ -z $SITE_BASE]; then
    SITE_BASE="$(dirname "$_script_dir/..")"
fi

# Define TRACENV
TRACENV="$(dirname "$SITE_BASE/tracenv")"

