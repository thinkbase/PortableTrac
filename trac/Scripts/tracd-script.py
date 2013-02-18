#!"I:\thinkbase.net\github\PortableTrac-git\Portable Python 2.7.3.1\App\python.exe"
# EASY-INSTALL-ENTRY-SCRIPT: 'Trac==1.0.1','console_scripts','tracd'
__requires__ = 'Trac==1.0.1'
import sys
from pkg_resources import load_entry_point

sys.exit(
   load_entry_point('Trac==1.0.1', 'console_scripts', 'tracd')()
)
