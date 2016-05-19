## inotify_init1 flags.

IN_CLOEXEC  = 0o2000000
IN_NONBLOCK = 0o0004000

## Supported events suitable for MASK parameter of INOTIFY_ADD_WATCH.

IN_ACCESS        = 0x00000001
IN_MODIFY        = 0x00000002
IN_ATTRIB        = 0x00000004
IN_CLOSE_WRITE   = 0x00000008
IN_CLOSE_NOWRITE = 0x00000010
IN_OPEN          = 0x00000020
IN_MOVED_FROM    = 0x00000040
IN_MOVED_TO      = 0x00000080
IN_CREATE        = 0x00000100
IN_DELETE        = 0x00000200
IN_DELETE_SELF   = 0x00000400
IN_MOVE_SELF     = 0x00000800

## Helper events.

IN_CLOSE         = (IN_CLOSE_WRITE | IN_CLOSE_NOWRITE)
IN_MOVE          = (IN_MOVED_FROM | IN_MOVED_TO)

## All events which a program can wait on.

IN_ALL_EVENTS    = (IN_ACCESS | IN_MODIFY | IN_ATTRIB | IN_CLOSE_WRITE |
                    IN_CLOSE_NOWRITE | IN_OPEN | IN_MOVED_FROM | IN_MOVED_TO | 
                    IN_CREATE | IN_DELETE | IN_DELETE_SELF | IN_MOVE_SELF)

## Events sent by kernel.

IN_UNMOUNT    = 0x00002000 # Backing fs was unmounted.
IN_Q_OVERFLOW = 0x00004000 # Event queued overflowed.
IN_IGNORED    = 0x00008000 # File was ignored.

## Special flags.

IN_ONLYDIR     = 0x01000000 # Only watch the path if it is a directory.
IN_DONT_FOLLOW = 0x02000000 # Do not follow a sym link.
IN_MASK_ADD    = 0x20000000 # Add to the mask of an already existing watch.
IN_ISDIR       = 0x40000000 # Event occurred against dir.
IN_ONESHOT     = 0x80000000 # Only send event once.

MASK_LOOKUP = {
    0o2000000: 'IN_CLOEXEC',
    0o0004000: 'IN_NONBLOCK',

    ## Supported events suitable for MASK parameter of INOTIFY_ADD_WATCH.

    0x00000001: 'IN_ACCESS',
    0x00000002: 'IN_MODIFY',
    0x00000004: 'IN_ATTRIB',
    0x00000008: 'IN_CLOSE_WRITE',
    0x00000010: 'IN_CLOSE_NOWRITE',
    0x00000020: 'IN_OPEN',
    0x00000040: 'IN_MOVED_FROM',
    0x00000080: 'IN_MOVED_TO',
    0x00000100: 'IN_CREATE',
    0x00000200: 'IN_DELETE',
    0x00000400: 'IN_DELETE_SELF',
    0x00000800: 'IN_MOVE_SELF',

    ## Events sent by kernel.

    0x00002000: 'IN_UNMOUNT',
    0x00004000: 'IN_Q_OVERFLOW',
    0x00008000: 'IN_IGNORED',

    ## Special flags.

    0x01000000: 'IN_ONLYDIR',
    0x02000000: 'IN_DONT_FOLLOW',
    0x20000000: 'IN_MASK_ADD',
    0x40000000: 'IN_ISDIR',
    0x80000000: 'IN_ONESHOT',
}
