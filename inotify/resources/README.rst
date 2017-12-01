|Build\_Status|
|Coverage\_Status|

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

    import inotify.adapters

    def _main():
        i = inotify.adapters.Inotify()

        i.add_watch('/tmp')

        with open('/tmp/test_file', 'w'):
            pass

        for event in i.event_gen(yield_nones=False):
            (_, type_names, path, filename) = event

            print("PATH=[{}] FILENAME=[{}] EVENT_TYPES={}".format(
                  path, filename, type_names))

    if __name__ == '__main__':
        _main()

Output::

    PATH=[/tmp] FILENAME=[test_file] EVENT_TYPES=['IN_MODIFY']
    PATH=[/tmp] FILENAME=[test_file] EVENT_TYPES=['IN_OPEN']
    PATH=[/tmp] FILENAME=[test_file] EVENT_TYPES=['IN_CLOSE_WRITE']
    ^CTraceback (most recent call last):
      File "inotify_test.py", line 18, in <module>
        _main()
      File "inotify_test.py", line 11, in _main
        for event in i.event_gen(yield_nones=False):
      File "/home/dustin/development/python/pyinotify/inotify/adapters.py", line 202, in event_gen
        events = self.__epoll.poll(block_duration_s)
    KeyboardInterrupt

Note that this works quite nicely, but, in the event that you don't want to be driven by the loop, you can also provide a timeout and then even flatten the output of the generator directly to a list::

    import inotify.adapters

    def _main():
        i = inotify.adapters.Inotify()

        i.add_watch('/tmp')

        with open('/tmp/test_file', 'w'):
            pass

        events = i.event_gen(yield_nones=False, timeout_s=1)
        events = list(events)

        print(events)

    if __name__ == '__main__':
        _main()

This will return everything that's happened since the last time you ran it (artificially formatted here)::

    [
        (_INOTIFY_EVENT(wd=1, mask=2, cookie=0, len=16), ['IN_MODIFY'], '/tmp', u'test_file'),
        (_INOTIFY_EVENT(wd=1, mask=32, cookie=0, len=16), ['IN_OPEN'], '/tmp', u'test_file'),
        (_INOTIFY_EVENT(wd=1, mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], '/tmp', u'test_file')
    ]

**Note that the event-loop will automatically register new folders to be watched, so, if you will create new folders and then potentially delete them, between calls, and are only retrieving the events in batches (like above) then you might experience issues. See the parameters for `event_gen()` for options to handle this scenario.**


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

- *epoll* is used to audit for *inotify* kernel events.

- **The earlier versions of this project had only partial Python 3 compatibility (string related). This required doing the string<->bytes conversions outside of this project. As of the current version, this has been fixed. However, this means that Python 3 users may experience breakages until this is compensated-for on their end. It will obviously be trivial for this project to detect the type of the arguments that are passed but there'd be no concrete way of knowing which type to return. Better to just fix it completely now and move forward.**

- You may also choose to pass the list of directories to watch via the *paths* parameter of the constructor. This would work best in situations where your list of paths is static.

- Calling `remove_watch()` is not strictly necessary. The *inotify* resources is automatically cleaned-up, which would clean-up all watch resources as well.


=======
Testing
=======

Call "test.sh" to run the tests::

    $ ./test.sh
    test__cycle (tests.test_inotify.TestInotify) ... ok
    test__get_event_names (tests.test_inotify.TestInotify) ... ok
    test__international_naming_python2 (tests.test_inotify.TestInotify) ... SKIP: Not in Python 2
    test__international_naming_python3 (tests.test_inotify.TestInotify) ... ok
    test__automatic_new_watches_on_existing_paths (tests.test_inotify.TestInotifyTree) ... ok
    test__automatic_new_watches_on_new_paths (tests.test_inotify.TestInotifyTree) ... ok
    test__cycle (tests.test_inotify.TestInotifyTree) ... ok
    test__renames (tests.test_inotify.TestInotifyTree) ... ok
    test__cycle (tests.test_inotify.TestInotifyTrees) ... ok

    ----------------------------------------------------------------------
    Ran 9 tests in 12.039s

    OK (SKIP=1)

.. |Build_Status| image:: https://travis-ci.org/dsoprea/PyInotify.svg?branch=master
   :target: https://travis-ci.org/dsoprea/PyInotify
.. |Coverage_Status| image:: https://coveralls.io/repos/github/dsoprea/PyInotify/badge.svg?branch=master
   :target: https://coveralls.io/github/dsoprea/PyInotify?branch=master
