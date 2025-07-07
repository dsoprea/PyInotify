# -*- coding: utf-8 -*-

import os
import unittest
import collections
import errno

import inotify.constants
import inotify.calls
import inotify.adapters
import inotify.test_support

try:
    unicode
except NameError:
    _HAS_PYTHON2_UNICODE_SUPPORT = False
else:
    _HAS_PYTHON2_UNICODE_SUPPORT = True


_INOTIFY_EVENT__NO_WD = \
    collections.namedtuple(
        '_INOTIFY_EVENT__NO_WD',
        [
            'mask',
            'cookie',
            'len',
        ])


def _strip_wd(events):
    """The descriptors are nondeterministic, so we need to remove them from the
    comparisons in order to stabilize testing.
    """

# TOOD(dustin): We've only currently implemented this in the tests that have required it

    events_stripped = []
    for header, type_names, path, filename in events:
        data = header._asdict()
        del data['wd']

        header_stripped = _INOTIFY_EVENT__NO_WD(**data)
        events_stripped.append((header_stripped, type_names, path, filename))


    return events_stripped


class TestInotify(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.maxDiff = None

        super(TestInotify, self).__init__(*args, **kwargs)

    def __read_all_events(self, i):
        events = list(i.event_gen(timeout_s=1, yield_nones=False))
        return events

    @unittest.skipIf(_HAS_PYTHON2_UNICODE_SUPPORT is True, "Not in Python 3")
    def test__international_naming_python3(self):
        with inotify.test_support.temp_path() as path:
            inner_path = os.path.join(path, '新增資料夾')
            os.mkdir(inner_path)

            i = inotify.adapters.Inotify()
            i.add_watch(inner_path)

            with open(os.path.join(inner_path, 'filename'), 'w'):
                pass

            events = self.__read_all_events(i)

            expected = [
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=256, cookie=0, len=16), ['IN_CREATE'], inner_path, 'filename'),
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=32, cookie=0, len=16), ['IN_OPEN'], inner_path, 'filename'),
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], inner_path, 'filename'),
            ]

            self.assertEqual(events, expected)

    @unittest.skipIf(_HAS_PYTHON2_UNICODE_SUPPORT is False, "Not in Python 2")
    def test__international_naming_python2(self):
        with inotify.test_support.temp_path() as path:
            inner_path = os.path.join(unicode(path), u'新增資料夾')
            os.mkdir(inner_path)

            i = inotify.adapters.Inotify()
            i.add_watch(inner_path)

            with open(os.path.join(inner_path, u'filename料夾'), 'w'):
                pass

            events = self.__read_all_events(i)

            expected = [
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=256, cookie=0, len=16), ['IN_CREATE'], inner_path, u'filename料夾'),
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=32, cookie=0, len=16), ['IN_OPEN'], inner_path, u'filename料夾'),
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], inner_path, u'filename料夾'),
            ]

            self.assertEqual(events, expected)

    def test__cycle(self):
        with inotify.test_support.temp_path() as path:
            path1 = os.path.join(path, 'aa')
            os.mkdir(path1)

            path2 = os.path.join(path, 'bb')
            os.mkdir(path2)

            i = inotify.adapters.Inotify()
            i.add_watch(path1)

            with open('ignored_new_file', 'w'):
                pass

            with open(os.path.join(path1, 'seen_new_file'), 'w'):
                pass

            with open(os.path.join(path2, 'ignored_new_file'), 'w'):
                pass

            os.remove(os.path.join(path1, 'seen_new_file'))

            events = self.__read_all_events(i)

            expected = [
                (
                    inotify.adapters._INOTIFY_EVENT(wd=1, mask=256, cookie=0, len=16),
                    ['IN_CREATE'],
                    path1,
                    'seen_new_file'
                ),
                (
                    inotify.adapters._INOTIFY_EVENT(wd=1, mask=32, cookie=0, len=16),
                    ['IN_OPEN'],
                    path1,
                    'seen_new_file'
                ),
                (
                    inotify.adapters._INOTIFY_EVENT(wd=1, mask=8, cookie=0, len=16),
                    ['IN_CLOSE_WRITE'],
                    path1,
                    'seen_new_file'
                ),
                (
                    inotify.adapters._INOTIFY_EVENT(wd=1, mask=512, cookie=0, len=16),
                    ['IN_DELETE'],
                    path1,
                    'seen_new_file'
                )
            ]

            self.assertEqual(events, expected)

            # This can't be removed until *after* we've read the events because
            # they'll be flushed the moment we remove the watch.
            i.remove_watch(path1)

            with open(os.path.join(path1, 'ignored_after_removal'), 'w'):
                pass

            events = self.__read_all_events(i)
            self.assertEqual(events, [])

    @staticmethod
    def _open_write_close(*args):
        with open(os.path.join(*args), 'w'):
            pass

    @staticmethod
    def _make_temp_path(*args):
        path = os.path.join(*args)
        os.mkdir(path)
        return path

    @staticmethod
    def _event_general(wd, mask, type_name, path, filename):
        return ((inotify.adapters._INOTIFY_EVENT(wd=wd, mask=mask, cookie=0, len=16)),
                [type_name],
                path,
                filename)

    @staticmethod
    def _event_create(wd, path, filename):
        return TestInotify._event_general(wd, 256, 'IN_CREATE', path, filename)

    @staticmethod
    def _event_open(wd, path, filename):
        return TestInotify._event_general(wd, 32, 'IN_OPEN', path, filename)

    @staticmethod
    def _event_close_write(wd, path, filename):
        return TestInotify._event_general(wd, 8, 'IN_CLOSE_WRITE', path, filename)

    def test__watch_list_of_paths(self):
        with inotify.test_support.temp_path() as path:
            path1 = TestInotify._make_temp_path(path, 'aa')
            path2 = TestInotify._make_temp_path(path, 'bb')
            i = inotify.adapters.Inotify([path1, path2])
            TestInotify._open_write_close('ignored_new_file')
            TestInotify._open_write_close(path1, 'seen_new_file')
            TestInotify._open_write_close(path2, 'seen_new_file2')
            os.remove(os.path.join(path1, 'seen_new_file'))
            events = self.__read_all_events(i)
            expected = [
                TestInotify._event_create(wd=1, path=path1, filename='seen_new_file'),
                TestInotify._event_open(wd=1, path=path1, filename='seen_new_file'),
                TestInotify._event_close_write(wd=1, path=path1, filename='seen_new_file'),
                TestInotify._event_create(wd=2, path=path2, filename='seen_new_file2'),
                TestInotify._event_open(wd=2, path=path2, filename='seen_new_file2'),
                TestInotify._event_close_write(wd=2, path=path2, filename='seen_new_file2'),
                TestInotify._event_general(wd=1, mask=512, type_name='IN_DELETE',
                                           path=path1, filename='seen_new_file')
            ]
            self.assertEqual(events, expected)

    def test__error_on_watch_nonexistent_folder(self):
        i = inotify.adapters.Inotify()

        try:
            i.add_watch('/dev/null/foo')

        except inotify.calls.InotifyError as ie:
            self.assertEqual(ie.errno, errno.ENOTDIR)
            self.assertEqual(ie.errmsg, 'Not a directory')

        else:
            raise Exception("Expected exception.")

    def test__get_event_names(self):
        all_mask = 0
        for bit in inotify.constants.MASK_LOOKUP.keys():
            all_mask |= bit

        all_names = inotify.constants.MASK_LOOKUP.values()
        all_names = list(all_names)

        i = inotify.adapters.Inotify()
        names = i._get_event_names(all_mask)

        self.assertEqual(names, all_names)


class TestInotifyTree(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.maxDiff = None

        super(TestInotifyTree, self).__init__(*args, **kwargs)

    def __read_all_events(self, i):
        events = list(i.event_gen(timeout_s=1, yield_nones=False))
        return events

    def test__cycle(self):
        with inotify.test_support.temp_path() as path:
            path1 = os.path.join(path, 'aa')
            os.mkdir(path1)

            path2 = os.path.join(path, 'bb')
            os.mkdir(path2)

            i = inotify.adapters.InotifyTree(path)

            with open('seen_new_file1', 'w'):
                pass

            with open(os.path.join(path1, 'seen_new_file2'), 'w'):
                pass

            with open(os.path.join(path2, 'seen_new_file3'), 'w'):
                pass

            os.remove(os.path.join(path, 'seen_new_file1'))
            os.remove(os.path.join(path1, 'seen_new_file2'))
            os.remove(os.path.join(path2, 'seen_new_file3'))

            os.rmdir(path1)
            os.rmdir(path2)

            events = self.__read_all_events(i)
            events_stripped = _strip_wd(events)

            expected = [
                (_INOTIFY_EVENT__NO_WD(mask=256, cookie=0, len=16), ['IN_CREATE'], path, 'seen_new_file1'),
                (_INOTIFY_EVENT__NO_WD(mask=32, cookie=0, len=16), ['IN_OPEN'], path, 'seen_new_file1'),
                (_INOTIFY_EVENT__NO_WD(mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], path, 'seen_new_file1'),

                (_INOTIFY_EVENT__NO_WD(mask=256, cookie=0, len=16), ['IN_CREATE'], path1, 'seen_new_file2'),
                (_INOTIFY_EVENT__NO_WD(mask=32, cookie=0, len=16), ['IN_OPEN'], path1, 'seen_new_file2'),
                (_INOTIFY_EVENT__NO_WD(mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], path1, 'seen_new_file2'),

                (_INOTIFY_EVENT__NO_WD(mask=256, cookie=0, len=16), ['IN_CREATE'], path2, 'seen_new_file3'),
                (_INOTIFY_EVENT__NO_WD(mask=32, cookie=0, len=16), ['IN_OPEN'], path2, 'seen_new_file3'),
                (_INOTIFY_EVENT__NO_WD(mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], path2, 'seen_new_file3'),

                (_INOTIFY_EVENT__NO_WD(mask=512, cookie=0, len=16), ['IN_DELETE'], path, 'seen_new_file1'),
                (_INOTIFY_EVENT__NO_WD(mask=512, cookie=0, len=16), ['IN_DELETE'], path1, 'seen_new_file2'),
                (_INOTIFY_EVENT__NO_WD(mask=512, cookie=0, len=16), ['IN_DELETE'], path2, 'seen_new_file3'),

                (_INOTIFY_EVENT__NO_WD(mask=1024, cookie=0, len=0), ['IN_DELETE_SELF'], path1, ''),
                (_INOTIFY_EVENT__NO_WD(mask=32768, cookie=0, len=0), ['IN_IGNORED'], path1, ''),
                (_INOTIFY_EVENT__NO_WD(mask=1073742336, cookie=0, len=16), ['IN_DELETE', 'IN_ISDIR'], path, 'aa'),

                (_INOTIFY_EVENT__NO_WD(mask=1024, cookie=0, len=0), ['IN_DELETE_SELF'], path2, ''),
                (_INOTIFY_EVENT__NO_WD(mask=32768, cookie=0, len=0), ['IN_IGNORED'], path2, ''),
                (_INOTIFY_EVENT__NO_WD(mask=1073742336, cookie=0, len=16), ['IN_DELETE', 'IN_ISDIR'], path, 'bb'),
            ]

            self.assertEqual(events_stripped, expected)

    def test__renames(self):

        # Since we're not reading the events one at a time in a loop and
        # removing or renaming folders will flush any queued events, we have to
        # group things in order to check things first before such operations.

        with inotify.test_support.temp_path() as path:
            i = inotify.adapters.InotifyTree(path)

            old_path = os.path.join(path, 'old_folder')
            new_path = os.path.join(path, 'new_folder')

            os.mkdir(old_path)

            events1 = self.__read_all_events(i)

            for event in events1:
                event[1].sort()

            expected = [
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=1073742080, cookie=events1[0][0].cookie, len=16), ['IN_CREATE', 'IN_ISDIR'], path, 'old_folder'),
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=1073741856, cookie=0, len=16), ['IN_ISDIR', 'IN_OPEN'], path, 'old_folder'),
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=1073741825, cookie=0, len=16), ['IN_ACCESS', 'IN_ISDIR'], path, 'old_folder'),
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=1073741840, cookie=0, len=16), ['IN_CLOSE_NOWRITE', 'IN_ISDIR'], path, 'old_folder')
            ]

            self.assertEqual(events1, expected)


            os.rename(old_path, new_path)

            events2 = self.__read_all_events(i)

            for event in events2:
                event[1].sort()

            expected = [
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=1073741825, cookie=0, len=16), ['IN_ACCESS', 'IN_ISDIR'], path, 'new_folder'),
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=1073741825, cookie=0, len=16), ['IN_ACCESS', 'IN_ISDIR'], path, 'new_folder'),
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=1073741840, cookie=0, len=16), ['IN_CLOSE_NOWRITE', 'IN_ISDIR'], path, 'new_folder'),
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=1073741856, cookie=0, len=16), ['IN_ISDIR', 'IN_OPEN'], path, 'new_folder'),

                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=1073741888, cookie=events2[0][0].cookie, len=16), ['IN_ISDIR', 'IN_MOVED_FROM'], path, 'old_folder'),
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=1073741952, cookie=events2[1][0].cookie, len=16), ['IN_ISDIR', 'IN_MOVED_TO'], path, 'new_folder'),
                (inotify.adapters._INOTIFY_EVENT(wd=2, mask=2048, cookie=0, len=0), ['IN_MOVE_SELF'], os.path.join(path, 'new_folder'), ''),

                (inotify.adapters._INOTIFY_EVENT(wd=2, mask=1073741825, cookie=0, len=0), ['IN_ACCESS', 'IN_ISDIR'], os.path.join(path, 'new_folder'), ''),
                (inotify.adapters._INOTIFY_EVENT(wd=2, mask=1073741825, cookie=0, len=0), ['IN_ACCESS', 'IN_ISDIR'], os.path.join(path, 'new_folder'), ''),
                (inotify.adapters._INOTIFY_EVENT(wd=2, mask=1073741840, cookie=0, len=0), ['IN_CLOSE_NOWRITE', 'IN_ISDIR'], os.path.join(path, 'new_folder'), ''),
                (inotify.adapters._INOTIFY_EVENT(wd=2, mask=1073741856, cookie=0, len=0), ['IN_ISDIR', 'IN_OPEN'], os.path.join(path, 'new_folder'), ''),
            ]

            self.assertEqual(sorted(events2), sorted(expected))


            with open(os.path.join(new_path, 'old_filename'), 'w'):
                pass

            os.rename(
                os.path.join(new_path, 'old_filename'),
                os.path.join(new_path, 'new_filename'))

            os.remove(os.path.join('new_folder', 'new_filename'))
            os.rmdir('new_folder')

            events3 = self.__read_all_events(i)

            for event in events3:
                event[1].sort()

            expected = [
                (inotify.adapters._INOTIFY_EVENT(wd=2, mask=256, cookie=0, len=16), ['IN_CREATE'], new_path, 'old_filename'),
                (inotify.adapters._INOTIFY_EVENT(wd=2, mask=32, cookie=0, len=16), ['IN_OPEN'], new_path, 'old_filename'),
                (inotify.adapters._INOTIFY_EVENT(wd=2, mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], new_path, 'old_filename'),

                (inotify.adapters._INOTIFY_EVENT(wd=2, mask=64, cookie=events3[3][0].cookie, len=16), ['IN_MOVED_FROM'], new_path, 'old_filename'),
                (inotify.adapters._INOTIFY_EVENT(wd=2, mask=128, cookie=events3[4][0].cookie, len=16), ['IN_MOVED_TO'], new_path, 'new_filename'),

                (inotify.adapters._INOTIFY_EVENT(wd=2, mask=512, cookie=0, len=16), ['IN_DELETE'], new_path, 'new_filename'),

                (inotify.adapters._INOTIFY_EVENT(wd=2, mask=1024, cookie=0, len=0), ['IN_DELETE_SELF'], new_path, ''),
                (inotify.adapters._INOTIFY_EVENT(wd=2, mask=32768, cookie=0, len=0), ['IN_IGNORED'], new_path, ''),
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=1073742336, cookie=0, len=16), ['IN_DELETE', 'IN_ISDIR'], path, 'new_folder'),
            ]

            self.assertEqual(sorted(events3), sorted(expected))

    def test__automatic_new_watches_on_new_paths(self):

        # Tests that watches are actively established as new folders are
        # created.

        with inotify.test_support.temp_path() as path:
            i = inotify.adapters.InotifyTree(path)

            path1 = os.path.join(path, 'folder1')
            path2 = os.path.join(path1, 'folder2')

            os.mkdir(path1)

            events = self.__read_all_events(i)

            for event in events:
                event[1].sort()

            expected = [
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=1073742080, cookie=0, len=16), ['IN_CREATE', 'IN_ISDIR'], path, 'folder1'),
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=1073741856, cookie=0, len=16), ['IN_ISDIR', 'IN_OPEN'], path, 'folder1'),
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=1073741825, cookie=0, len=16), ['IN_ACCESS', 'IN_ISDIR'], path, 'folder1'),
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=1073741840, cookie=0, len=16), ['IN_CLOSE_NOWRITE', 'IN_ISDIR'], path, 'folder1'),
            ]

            self.assertEqual(events, expected)


            os.mkdir(path2)

            events = self.__read_all_events(i)

            for event in events:
                event[1].sort()

            expected = [
                (inotify.adapters._INOTIFY_EVENT(wd=2, mask=1073742080, cookie=0, len=16), ['IN_CREATE', 'IN_ISDIR'], path1, 'folder2'),
                (inotify.adapters._INOTIFY_EVENT(wd=2, mask=1073741856, cookie=0, len=16), ['IN_ISDIR', 'IN_OPEN'], path1, 'folder2'),
                (inotify.adapters._INOTIFY_EVENT(wd=2, mask=1073741825, cookie=0, len=16), ['IN_ACCESS', 'IN_ISDIR'], path1, 'folder2'),
                (inotify.adapters._INOTIFY_EVENT(wd=2, mask=1073741840, cookie=0, len=16), ['IN_CLOSE_NOWRITE', 'IN_ISDIR'], path1, 'folder2'),
            ]

            self.assertEqual(events, expected)


            with open(os.path.join(path2,'filename'), 'w'):
                pass

            events = self.__read_all_events(i)

            expected = [
                (inotify.adapters._INOTIFY_EVENT(wd=3, mask=256, cookie=0, len=16), ['IN_CREATE'], path2, 'filename'),
                (inotify.adapters._INOTIFY_EVENT(wd=3, mask=32, cookie=0, len=16), ['IN_OPEN'], path2, 'filename'),
                (inotify.adapters._INOTIFY_EVENT(wd=3, mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], path2, 'filename'),
            ]

            self.assertEqual(events, expected)

    def test__automatic_new_watches_on_existing_paths(self):

        # Tests whether the watches are recursively established when we
        # initialize.

        with inotify.test_support.temp_path() as path:
            path1 = os.path.join(path, 'folder1')
            path2 = os.path.join(path1, 'folder2')

            os.mkdir(path1)
            os.mkdir(path2)

            i = inotify.adapters.InotifyTree(path)

            with open(os.path.join(path2,'filename'), 'w'):
                pass

            events = self.__read_all_events(i)

            expected = [
                (inotify.adapters._INOTIFY_EVENT(wd=3, mask=256, cookie=0, len=16), ['IN_CREATE'], path2, 'filename'),
                (inotify.adapters._INOTIFY_EVENT(wd=3, mask=32, cookie=0, len=16), ['IN_OPEN'], path2, 'filename'),
                (inotify.adapters._INOTIFY_EVENT(wd=3, mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], path2, 'filename'),
            ]

            self.assertEqual(events, expected)


class TestInotifyTrees(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.maxDiff = None

        super(TestInotifyTrees, self).__init__(*args, **kwargs)

    def __read_all_events(self, i):
        events = list(i.event_gen(timeout_s=1, yield_nones=False))
        return events

    def test__cycle(self):
        with inotify.test_support.temp_path() as path:
            path1 = os.path.join(path, 'aa')
            os.mkdir(path1)

            path2 = os.path.join(path, 'bb')
            os.mkdir(path2)

            i = inotify.adapters.InotifyTrees([path1, path2])

            with open(os.path.join(path1, 'seen_new_file1'), 'w'):
                pass

            with open(os.path.join(path2, 'seen_new_file2'), 'w'):
                pass

            events = self.__read_all_events(i)

            expected = [
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=256, cookie=0, len=16), ['IN_CREATE'], path1, 'seen_new_file1'),
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=32, cookie=0, len=16), ['IN_OPEN'], path1, 'seen_new_file1'),
                (inotify.adapters._INOTIFY_EVENT(wd=1, mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], path1, 'seen_new_file1'),

                (inotify.adapters._INOTIFY_EVENT(wd=2, mask=256, cookie=0, len=16), ['IN_CREATE'], path2, 'seen_new_file2'),
                (inotify.adapters._INOTIFY_EVENT(wd=2, mask=32, cookie=0, len=16), ['IN_OPEN'], path2, 'seen_new_file2'),
                (inotify.adapters._INOTIFY_EVENT(wd=2, mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], path2, 'seen_new_file2'),
            ]

            self.assertEqual(events, expected)
