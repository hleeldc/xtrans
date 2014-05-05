import os
import sys

__all__ = ["capabilities"]

capabilities = {
    "playback":False,
    "spellchecker":False,
}    

if sys.platform.startswith('linux') or \
   sys.platform.startswith('freebsd'):
    import ossaudiodev
    try:
        a = ossaudiodev.open("/dev/dsp", "rw")
        a.close()
        capabilities["playback"] = True
    except IOError:
        pass
elif sys.platform == 'win32':
    capabilities["playback"] = True

try:
    import aspell
    capabilities["spellchecker"] = True
except ImportError:
    pass


    
