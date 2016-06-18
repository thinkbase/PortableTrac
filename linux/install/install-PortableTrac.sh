#! /bin/bash
set -o nounset
set -o errexit

# Get the directory of current shell, so we can calculate the "site-packages" path in git repo.
if [ -z $BASH ]; then
    echo "This shell script MUST run under bash."
    exit /b -1
fi
_script="$(readlink -f "${BASH_SOURCE[0]}")"
_script_dir="$(dirname "$_script")"
echo "Directory of $_script : $_script_dir"

SITE_PKGS_DIR=$_script_dir/../../trac/Lib/site-packages

# Pre-install PIL
easy_install $_script_dir/PIL/Imaging-1.1.7.tar.gz
# Pre-install PyYAML
easy_install $_script_dir/PyYAML/PyYAML-3.11.tar.gz

# Install trac and plugins ...
easy_install ${SITE_PKGS_DIR}/Pygments-1.5-py2.7.egg
easy_install ${SITE_PKGS_DIR}/python_dateutil-2.1-py2.7.egg
easy_install ${SITE_PKGS_DIR}/pytz-2012h-py2.7.egg
easy_install ${SITE_PKGS_DIR}/simplejson-2.6.2-py2.7.egg
easy_install ${SITE_PKGS_DIR}/six-1.2.0-py2.7.egg

easy_install ${SITE_PKGS_DIR}/Babel-0.9.6-py2.7.egg
easy_install ${SITE_PKGS_DIR}/Trac-1.0.5.tar.gz

easy_install ${SITE_PKGS_DIR}/add_static_resources_plugin-0.0.3-py2.7.egg
easy_install ${SITE_PKGS_DIR}/autocompleteusers-0.4.2dev_r11757-py2.7.egg
easy_install ${SITE_PKGS_DIR}/codeexamplemacro-1.0_r11766-py2.7.egg
easy_install ${SITE_PKGS_DIR}/codeexamplemacro-1.0_r11766-py2.7-patched.egg
easy_install ${SITE_PKGS_DIR}/docutils-0.9.1-py2.7.egg
easy_install ${SITE_PKGS_DIR}/gantt-0.2-py2.7.egg
easy_install ${SITE_PKGS_DIR}/graphviz-1.0.0.7dev_r12290-py2.7.egg
easy_install ${SITE_PKGS_DIR}/gridmodify-0.1.6dev_r12235-py2.7.egg
easy_install ${SITE_PKGS_DIR}/macrochain-0.2-py2.7.egg
easy_install ${SITE_PKGS_DIR}/notebox-1.0dev_r11779-py2.7.egg
easy_install ${SITE_PKGS_DIR}/plantuml-2.0dev_r11721-py2.7.egg
easy_install ${SITE_PKGS_DIR}/plantuml-2.0dev_r11721-py2.7-patched.egg

#FIXME: projectplan need trac>0.11 <0.13
#easy_install ${SITE_PKGS_DIR}/projectplan-0.93.0-py2.7.egg
#easy_install ${SITE_PKGS_DIR}/projectplan-0.93.0-py2.7-patched.egg

easy_install ${SITE_PKGS_DIR}/tracaccountmanager-0.4dev_r12139-py2.7.egg

#tracaddcommentmacro depends on tracmacropost
easy_install ${SITE_PKGS_DIR}/tracmacropost-0.2-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracaddcommentmacro-0.3-py2.7.egg

easy_install ${SITE_PKGS_DIR}/tracaddheadersplugin-0.3-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracadvparseargsplugin-0.4-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracautocomplete-0.1-py2.7.egg
easy_install ${SITE_PKGS_DIR}/traccodecomments-1.1.1-py2.7.egg
easy_install ${SITE_PKGS_DIR}/traccsvmacro-1.0-py2.7.egg
easy_install ${SITE_PKGS_DIR}/traccustomfieldadmin-0.2.8_r12166-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracdatefield-3.0.0dev_r12118-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracdragdrop-0.12.0.10_r12033-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracflashembedmacro-0.95rc1_r10984-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracfullblogplugin-0.1.1_r12111-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracganttcalendarplugin-0.11-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracincludemacro-3.0.0dev_r12030-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracincludepagesmacro-0.1-py2.7.egg
easy_install ${SITE_PKGS_DIR}/trac_jsgantt-0.10_r12213-py2.7.egg
easy_install ${SITE_PKGS_DIR}/trackeywordsuggest-0.5.0dev_r12103-py2.7.egg
easy_install ${SITE_PKGS_DIR}/trac_lightertheme-0.3-py2.7.egg
easy_install ${SITE_PKGS_DIR}/traclistofwikipagesmacro-0.4-py2.7.egg

easy_install ${SITE_PKGS_DIR}/tracmastertickets-3.0.3-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracmastertickets-3.0.3-py2.7-patched.egg

easy_install ${SITE_PKGS_DIR}/tracnavcontrol-1.0-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracnewpagemacro-0.1-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracnumberedheadlinesplugin-0.4_r10976-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracreportinplaceeditplugin-0.1-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracsectioneditplugin-0.2.6_r11208-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracsql-0.3-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracstats-0.5-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracsubpages-0.5-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracsubticketsplugin-0.2.0.dev_20121107-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tractags-0.6-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tractags-0.6-py2.7-patched.egg
easy_install ${SITE_PKGS_DIR}/tracthemeengine-2.1.0-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracticketchangelogplugin-0.1-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracticketdepgraph-0.11-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tractweakui-0.1-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracvote-0.1.3dev_r11793-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracwikistats-0.1_r11352-py2.7.egg
easy_install ${SITE_PKGS_DIR}/trac_workflownotificationplugin-0.4-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracwysiwyg-0.12.0.4_r11158-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracxmlrpc-1.1.2_r13203-py2.7.egg
easy_install ${SITE_PKGS_DIR}/visitcounter-0.2-py2.7.egg
#easy_install ${SITE_PKGS_DIR}/wikitablemacro-0.1_r10997-py2.7.egg
easy_install ${SITE_PKGS_DIR}/workfloweditorplugin-1.1.6_r12220-py2.7.egg

easy_install ${SITE_PKGS_DIR}/tracprojectmenu-2.0dev_r14054-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracsqlhelper-0.3.0-py2.7.egg
easy_install ${SITE_PKGS_DIR}/trac_multireposearchplugin-0.6-py2.7.egg
easy_install ${SITE_PKGS_DIR}/readmerendererplugin-0.1-py2.7.egg
easy_install ${SITE_PKGS_DIR}/readmerendererplugin-0.1-py2.7-patched.egg

easy_install ${SITE_PKGS_DIR}/wikitablemacro-0.3dev-py2.7.egg
easy_install ${SITE_PKGS_DIR}/tracusernamedecorateplugin-0.12.0.1-py2.7.egg
easy_install ${SITE_PKGS_DIR}/traccollapsibleplugin-0.1-py2.7.egg
