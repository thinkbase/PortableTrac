#!"E:\PortableTrac\Portable Python 2.7.3.1\App\python.exe"
# EASY-INSTALL-ENTRY-SCRIPT: 'tracsubticketsplugin==0.2.0.dev-20121107','console_scripts','check-trac-subtickets'
__requires__ = 'tracsubticketsplugin==0.2.0.dev-20121107'
import sys
from pkg_resources import load_entry_point

sys.exit(
   load_entry_point('tracsubticketsplugin==0.2.0.dev-20121107', 'console_scripts', 'check-trac-subtickets')()
)
