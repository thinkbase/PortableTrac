#! /bin/bash
set -o nounset
set -o errexit

source $(cd "$(dirname "$0")"; pwd)/bin/init-env.sh

DIGEST_FILE="$TRACENV/../protected/passwd"
AUTH="*,$DIGEST_FILE,trac"

set +o nounset
PORT="$1"
if [ -z $PORT ]
then
    echo -e "\nError: 1st argument(web server port number) missing.\n"
    exit -10
fi
ENV="$2"
if [ -z $ENV ]
then
    echo -e "\n2nd argument(trac environment) missing, running with ALL environments.\n"
    set -x
    tracd -p $PORT --auth="$AUTH" --env-parent-dir "$TRACENV"
else
    PRJ="$TRACENV/$ENV"
    if [ ! -d "$PRJ" ]
    then
        echo -e "\nRestore trac environment to ($PRJ) before start tracd ...\n"
        set -x
        chmod +x $PORTABLE_HOME/bin/do_restore.sh
        $PORTABLE_HOME/bin/do_restore.sh $ENV
        set +x
    fi
    if [ ! -d "$PRJ" ]
    then
        echo -e "\nError: trac environment ($PRJ) not found.\n"
        exit -20
    fi
    if [ ! -f "$DIGEST_FILE" ]
    then
        echo -e "\nError: passwd file missing, please run './passwd.sh admin 111111' to create it.\n"
        exit -30
    fi
    set -x
    tracd -p $PORT --auth="$AUTH" "$PRJ"
    set +x
fi

