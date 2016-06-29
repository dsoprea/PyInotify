========
Overview
========

*inotify* functionality is available from the Linux kernel and allows you to register one or more directories for watching, and to simply block and wait for notification events. This is obviously far more efficient than polling one or more directories to determine if anything has changed. This is available in the Linux kernel as of version 2.6 .

We've designed this library to act as a generator. All you have to do is loop, and you'll see one event at a time and block in-between. After each cycle (all notified events were processed, or no events were received), you'll get a *None*. You may use this as an opportunity to perform other tasks, if your application is being primarily driven by *inotify* events. By default, we'll only block for one-second on queries to the kernel. This may be set to something else by passing a seconds-value into the constructor as *block_duration_s*.

**This project is unrelated to the *PyInotify* project that existed prior to this one (this project began in 2015). That project is defunct and no longer available.**


==========
Installing
==========

Install via *pip*::

    $ sudo pip install inotify


=======
Example
=======

Code::

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
        i = inotify.adapters.Inotify()

        i.add_watch(b'/tmp')

        try:
            for event in i.event_gen():
                if event is not None:
                    (header, type_names, watch_path, filename) = event
                    _LOGGER.info("WD=(%d) MASK=(%d) COOKIE=(%d) LEN=(%d) MASK->NAMES=%s "
                                 "WATCH-PATH=[%s] FILENAME=[%s]", 
                                 header.wd, header.mask, header.cookie, header.len, type_names, 
                                 watch_path.decode('utf-8'), filename.decode('utf-8'))
        finally:
            i.remove_watch(b'/tmp')

    if __name__ == '__main__':
        _configure_logging()
        _main()

You may also choose to pass the list of directories to watch via the *paths* parameter of the constructor. This would work best in situations where your list of paths is static. Also, the remove_watch() call is included in the example, but is not strictly necessary. The *inotify* resources is cleaned-up, which would clean-up any *inotify*-internal watch resources as well.

Note that the directories to pass to the add_watch() and remove_watch() functions must be bytestring (in Python 3).  The same holds for the contents of the events that are returned.  It's up to the user to encode and decode any strings.

Directory operations to raise events::

    $ touch /tmp/aa
    $ rm /tmp/aa
    $ mkdir /tmp/dir1
    $ rmdir /tmp/dir1

Screen output from the code, above::

    2015-04-24 05:02:06,667 - __main__ - INFO - WD=(1) MASK=(256) COOKIE=(0) LEN=(16) MASK->NAMES=['IN_CREATE'] FILENAME=[aa]
    2015-04-24 05:02:06,667 - __main__ - INFO - WD=(1) MASK=(32) COOKIE=(0) LEN=(16) MASK->NAMES=['IN_OPEN'] FILENAME=[aa]
    2015-04-24 05:02:06,667 - __main__ - INFO - WD=(1) MASK=(4) COOKIE=(0) LEN=(16) MASK->NAMES=['IN_ATTRIB'] FILENAME=[aa]
    2015-04-24 05:02:06,667 - __main__ - INFO - WD=(1) MASK=(8) COOKIE=(0) LEN=(16) MASK->NAMES=['IN_CLOSE_WRITE'] FILENAME=[aa]
    2015-04-24 05:02:17,412 - __main__ - INFO - WD=(1) MASK=(512) COOKIE=(0) LEN=(16) MASK->NAMES=['IN_DELETE'] FILENAME=[aa]
    2015-04-24 05:02:22,884 - __main__ - INFO - WD=(1) MASK=(1073742080) COOKIE=(0) LEN=(16) MASK->NAMES=['IN_ISDIR', 'IN_CREATE'] FILENAME=[dir1]
    2015-04-24 05:02:25,948 - __main__ - INFO - WD=(1) MASK=(1073742336) COOKIE=(0) LEN=(16) MASK->NAMES=['IN_ISDIR', 'IN_DELETE'] FILENAME=[dir1]


==================
Recursive Watching
==================

We also provide you with the ability to add a recursive watch on a path. It turns out that there's no low-cost way of doing this; That's the reason that this functionality isn't provided by the kernel. However, we recognize that this is, nonetheless, sometimes necessary.

Example::

    i = inotify.adapters.InotifyTree('/tmp/watch_tree')

    for event in i.event_gen():
        # Do stuff...

        pass

The only substantial difference is the type of object that was instantiated. Everything else is the same.

This will immediately recurse through the directory tree and add watches on all subdirectories. New directories will automatically have watches added for them and deleted directories will be cleaned-up.

The other differences from the standard functionality:

- You can't remove a watch since watches are automatically managed.
- Even if you provide a very restrictive mask that doesn't allow for directory create/delete events, the *IN_ISDIR*, *IN_CREATE*, and *IN_DELETE* flags will still be added.


=====
Notes
=====

- *epoll* is used to audit for *inotify* kernel events. This is the fastest file-descriptor "selecting" strategy.

- Due to the GIL locking considerations of Python (or any VM-based language), it is strongly recommended that, if you need to be performing other tasks *while* you're concurrently watching directories, you use *multiprocessing* to put the directory-watching in a process of its own and feed information back [via queue/pipe/etc..]. This is especially true whenever your application is blocking on kernel functionality. Python's VM will remain locked and all other threads in your application will cease to function until something raises an event in the directories that are being watched.
