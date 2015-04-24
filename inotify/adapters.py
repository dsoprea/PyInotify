import logging
import select
import os
import struct
import collections

import inotify.constants
import inotify.calls

# Constants.

_DEFAULT_EPOLL_BLOCK_DURATION_S = 1
_HEADER_STRUCT_FORMAT = 'iIII'

# Globals.

_LOGGER = logging.getLogger(__name__)

_INOTIFY_EVENT = collections.namedtuple(
                    '_INOTIFY_EVENT',
                    [
                        'wd',
                        'mask',
                        'cookie',
                        'len',
                    ])

_STRUCT_HEADER_LENGTH = struct.calcsize(_HEADER_STRUCT_FORMAT)
_IS_DEBUG = bool(int(os.environ.get('DEBUG', '0')))


class Inotify(object):
    def __init__(self, paths=[], block_duration_s=_DEFAULT_EPOLL_BLOCK_DURATION_S):
        self.__block_duration_s = block_duration_s
        self.__watches = {}
        self.__buffer = ''

        self.__inotify_fd = inotify.calls.inotify_init()
        _LOGGER.debug("Inotify handle is (%d).", self.__inotify_fd)

        self.__epoll = select.epoll()

        self.__epoll.register(self.__inotify_fd, select.POLLIN)

        for path in paths:
            self.add_watch(path)

    def __del__(self):
        _LOGGER.debug("Cleaning-up inotify.")
        os.close(self.__inotify_fd)

    def add_watch(self, path, mask=inotify.constants.IN_ALL_EVENTS):
        wd = inotify.calls.inotify_add_watch(self.__inotify_fd, path, mask)
        _LOGGER.debug("Added watch (%d): [%s]", wd, path)

        self.__watches[path] = wd

    def remove_watch(self, path):
        wd = self.__watches[path]
        _LOGGER.debug("Removing watch for Inotify handle (%d) and watch-"
                      "handle (%d): [%s]", self.__inotify_fd, wd, path)

        inotify.calls.inotify_rm_watch(self.__inotify_fd, wd)

    def __get_event_names(self, event_type):
        names = []
        for bit, name in inotify.constants.MASK_LOOKUP.items():
            if event_type & bit:
                names.append(name)
                event_type -= bit

                if event_type == 0:
                    break

        assert event_type == 0, \
               "We could not resolve all event-types: (%d)" % (event_type,)

        return names

    def __handle_inotify_event(self, wd, event_type):
        """Handle a series of events coming-in from inotify."""

        names = self.__get_event_names(event_type)

        b = os.read(wd, 1024)
        if not b:
            return

        self.__buffer += b

        while 1:
            length = len(self.__buffer)

            if length < _STRUCT_HEADER_LENGTH:
                _LOGGER.debug("Not enough bytes for a header.")
                return

            # We have, at least, a whole-header in the buffer.

            peek_slice = self.__buffer[:_STRUCT_HEADER_LENGTH]

            header_raw = struct.unpack(
                            _HEADER_STRUCT_FORMAT, 
                            peek_slice)

            header = _INOTIFY_EVENT(*header_raw)
            type_names = self.__get_event_names(header.mask)

            event_length = (_STRUCT_HEADER_LENGTH + header.len)
            if length < event_length:
                return

            filename = self.__buffer[_STRUCT_HEADER_LENGTH:event_length]
            self.__buffer = self.__buffer[event_length:]

            yield (header, type_names, filename)

            buffer_length = len(self.__buffer)
            if buffer_length < _STRUCT_HEADER_LENGTH:
                break

    def event_gen(self):
        while True:
            events = self.__epoll.poll(self.__block_duration_s)
            for fd, event_type in events:
                for (header, type_names, filename) \
                        in self.__handle_inotify_event(fd, event_type):
                    yield (header, type_names, filename)

            yield None
