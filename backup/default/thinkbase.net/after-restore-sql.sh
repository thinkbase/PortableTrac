#! /bin/bash
set -o nounset
set -o errexit

# This script should create a sql script file for sqlite to execute after the restore process finished.

# $1 is the sql file's path, send by caller
set +o nounset
if [ ! -z $1 ]
then
    echo "UPDATE repository set value='${PORTABLE_HOME}/data/svn-testcase' WHERE id='1' AND name='dir';" > "$1"
    echo "UPDATE repository set value='svn:42be0d23-f3ec-7742-9214-b333e19b708d:'||'${PORTABLE_HOME}/data/svn-testcase' WHERE id='1' AND name='repository_dir';" >> "$1"
    
    echo -e "SQL Script File is $1 \n"
    set -x
    cat $1
    set +x
fi

