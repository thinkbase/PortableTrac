#! /bin/bash
set -o nounset
set -o errexit

source $(cd "$(dirname "$0")"; pwd)/bin/init-env.sh

for DIR in `ls "${SITE_BASE}/tracenv/"`
do
    if [ "${DIR:0:1}" = "." ]
    then
        echo "Skip dicectory: ${DIR}"
    else
        set -x
        trac-admin "${SITE_BASE}/tracenv/${DIR}" repository sync \*
        set +x
    fi
done

