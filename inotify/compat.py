"""Implements fsencode, fsdecode for python 2.3 <= 3.1.  os.fsdecode and os.decode were added
in python 3.2."""

import os
import sys

__all__ = ['fsencode', 'fsdecode']


def _fscodec():
    try:
        unicode
        err_msg = "expect bytes or str, not %s"
    except NameError:
        unicode = str
        err_msg = "expect str or unicode, not %s"
        
    encoding = sys.getfilesystemencoding()
    errors = 'strict' if encoding == 'mbcs' else 'surrogateescape'

    if hasattr(os, 'fsencode'):
        _fsencode = os.fsencode
    else:
        def _fsencode(filename):
            """
            Encode filename to the filesystem encoding with 'surrogateescape' error
            handler, return bytes unchanged. On Windows, use 'strict' error handler if
            the file system encoding is 'mbcs' (which is the default encoding).
            """
            if isinstance(filename, bytes):
                return filename
            elif isinstance(filename, unicode):
                return filename.encode(encoding, errors)
            else:
                raise TypeError(err_msg % type(filename).__name__)

    if hasattr(os, 'fsdecode'):
        _fsdecode = os.fsdecode
    else:
        def _fsdecode(filename):
            """
            Decode filename from the filesystem encoding with 'surrogateescape' error
            handler, return str unchanged. On Windows, use 'strict' error handler if
            the file system encoding is 'mbcs' (which is the default encoding).
            """
            if isinstance(filename, unicode):
                return filename
            elif isinstance(filename, bytes):
                return filename.decode(encoding, errors)
            else:
                raise TypeError(err_msg % type(filename).__name__)

    return _fsencode, _fsdecode

fsencode, fsdecode = _fscodec() # pylint: disable=invalid-name
del _fscodec
