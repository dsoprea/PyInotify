import os
import logging
import shutil
import tempfile
import contextlib

_LOGGER = logging.getLogger(__name__)

@contextlib.contextmanager
def temp_path():
    path = tempfile.mkdtemp()

    original_wd = os.getcwd()

    try:
        yield path
    finally:
        if os.path.exists(path) is True:
            shutil.rmtree(path)
