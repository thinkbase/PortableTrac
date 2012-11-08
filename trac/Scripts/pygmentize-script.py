#!"E:\PortableTrac\Portable Python 2.7.3.1\App\python.exe"
# EASY-INSTALL-ENTRY-SCRIPT: 'Pygments==1.5','console_scripts','pygmentize'
__requires__ = 'Pygments==1.5'
import sys
from pkg_resources import load_entry_point

sys.exit(
   load_entry_point('Pygments==1.5', 'console_scripts', 'pygmentize')()
)
