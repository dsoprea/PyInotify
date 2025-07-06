import ctypes
import ctypes.util

_FILEPATH = ctypes.util.find_library('c')
if _FILEPATH is None:
    _FILEPATH = 'libc.so.6'

instance = ctypes.CDLL(_FILEPATH, use_errno=True)
