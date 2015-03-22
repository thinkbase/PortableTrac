#! /bin/bash
set -o nounset
set -o errexit

source $(cd "$(dirname "$0")"; pwd)/bin/init-env.sh

set +o nounset
ENV="$1"
if [ -z $ENV ]
then
    echo -e "\nError: 1st argument[trac environment] missing.\n"
    exit -10
fi
set -o nounset

COPY_TARGET="$TRACENV/../backup/$ENV"
COPY_TARGET_OLD="$TRACENV/../backup/.old/$ENV.$TIMESTAMP"
if [ -d "$COPY_TARGET" ]
then
    mkdir -p "$COPY_TARGET_OLD"
    set -x
    mv "$COPY_TARGET" "$COPY_TARGET_OLD"
    set +x
fi

set -x
trac-admin "$TRACENV/$ENV" hotcopy "$COPY_TARGET"
echo .dump | sqlite3 "$COPY_TARGET/db/trac.db" > "$COPY_TARGET/trac-db.sql"
set +x
