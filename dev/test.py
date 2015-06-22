#!/usr/bin/env python2.7

import os.path
import sys
current_path = os.path.dirname(__file__)
dev_path = os.path.abspath(os.path.join(current_path, '..'))
sys.path.insert(0, dev_path)

import logging

import inotify.adapters

_DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

_LOGGER = logging.getLogger(__name__)

def _configure_logging():
    _LOGGER.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()

    formatter = logging.Formatter(_DEFAULT_LOG_FORMAT)
    ch.setFormatter(formatter)

    _LOGGER.addHandler(ch)

def _main():
#    paths = [
#        '/tmp',
#    ]
#    
#    i = Inotify(paths=paths)
    i = inotify.adapters.Inotify()

    i.add_watch('/tmp')

    try:
        for event in i.event_gen():
            if event is not None:
                (header, type_names, path, filename) = event
                _LOGGER.info("WD=(%d) MASK=(%d) COOKIE=(%d) LEN=(%d) MASK->NAMES=%s "
                             "FILENAME=[%s]", 
                             header.wd, header.mask, header.cookie, header.len, type_names, 
                             filename)
    finally:
        i.remove_watch('/tmp')

if __name__ == '__main__':
    _configure_logging()
    _main()
