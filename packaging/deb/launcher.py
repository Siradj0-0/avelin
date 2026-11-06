"""Launch the private system package, independently of the current directory."""
import runpy
import sys

sys.path.insert(0, '/usr/lib/avelin')
runpy.run_module('avelin', run_name='__main__', alter_sys=True)
