#!"E:\PortableTrac\Portable Python 2.7.3.1\App\python.exe"
# EASY-INSTALL-ENTRY-SCRIPT: 'trac==1.0','console_scripts','trac-admin'
__requires__ = 'trac==1.0'
import sys
from pkg_resources import load_entry_point

sys.exit(
   load_entry_point('trac==1.0', 'console_scripts', 'trac-admin')()
)
