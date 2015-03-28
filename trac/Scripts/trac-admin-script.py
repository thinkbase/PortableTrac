#!I:\thinkbase.net\github\PortableTrac\PortablePython\App\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'trac==1.0.5','console_scripts','trac-admin'
__requires__ = 'trac==1.0.5'
import sys
from pkg_resources import load_entry_point

sys.exit(
   load_entry_point('trac==1.0.5', 'console_scripts', 'trac-admin')()
)
