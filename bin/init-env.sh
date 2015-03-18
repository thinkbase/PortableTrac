# Get the directory of current shell, so we can calculate the "PortableTrac" path in git repo.
if [ -z $BASH ]; then
    echo "This shell script MUST run under bash."
    exit -1
fi
_script="$(readlink -f "${BASH_SOURCE[0]}")"
_script_dir="$(dirname "$_script")"
echo "Directory of $_script : $_script_dir"

set -o nounset
set -o errexit

# Define SITE_BASE
set +o nounset
if [ -z $SITE_BASE ]; then
    SITE_BASE=$(cd "$_script_dir/.."; pwd)
fi
set -o nounset

# Define PORTABLE_HOME
PORTABLE_HOME=$(cd "$_script_dir/.."; pwd)

# Define TRACENV
TRACENV="$SITE_BASE/tracenv"

# Define current timestamp
TIMESTAMP=`date "+%Y%m%d-%H%M%S"`

# Show system init info
echo "********************************************************************************"
echo "* PORTABLE_HOME = $PORTABLE_HOME"
echo "* SITE_BASE     = $SITE_BASE"
echo "* TRACENV       = $TRACENV"
echo "* TIMESTAMP     = $TIMESTAMP"
echo "********************************************************************************"

