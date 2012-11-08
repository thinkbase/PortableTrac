= About this software =
 * http://trac-hacks.org/wiki/TracReportInplaceEditPlugin
 * TracReportInplaceEditPlugin is a Trac plugin. 
 * Edit tickets in reports by inplace editor

= Install =
 You can install this software as normal Trac plugin.

 1. Uninstall TracReportInplaceEditPlugin if you have installed before.

 2. Change to the directory containning setup.py.
  * (Optional): If you are using Trac 0.12 with i18n, you should compile language files here:
 {{{
python setup.py compile_catalog -f
}}} 

 3. If you want to install this plugin globally, that will install this plugin to the python path:
  * python setup.py install

 4. If you want to install this plugin to trac instance only:
  * python setup.py bdist_egg
  * copy the generated egg file to the trac instance's plugin directory
  {{{
cp dist/*.egg /srv/trac/env/plugins
}}}

 5. Config trac.ini:
  {{{
[components]
ripe.* = enabled
}}}

= Prerequisite =
 * TBD

= Usage =
 * TBD
