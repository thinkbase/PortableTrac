#! /bin/bash
set -o nounset
set -o errexit

source $(cd "$(dirname "$0")"; pwd)/bin/init-env.sh

PASS_FILE="$TRACENV/../protected/passwd"
USER=$1
PASS=$2

set -x
python $PORTABLE_HOME/bin/trac-digest.py -u $USER -p $PASS >> $PASS_FILE
set +x

