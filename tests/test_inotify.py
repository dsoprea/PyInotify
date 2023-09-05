# -*- coding: utf-8 -*-

import os
import unittest
import time

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

# Inotify does not have a get for watch descriptors
# 
def get_wd(i, path):
    return i._Inotify__watches[path]


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
            inner_path = os.path.join(path, u'新增資料夾')
            os.mkdir(inner_path)

            i = inotify.adapters.Inotify()
            wd = i.add_watch(inner_path)

            with open(os.path.join(inner_path, 'filename'), 'w'):
                pass

            events = self.__read_all_events(i)

            expected = [
                (inotify.adapters._INOTIFY_EVENT(wd=wd, mask=256, cookie=0, len=16), ['IN_CREATE'], inner_path, 'filename'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd, mask=32, cookie=0, len=16), ['IN_OPEN'], inner_path, 'filename'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd, mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], inner_path, 'filename'),
            ]

            if events != expected:
                print("ACTUAL:")
                print("")

                for i, event in enumerate(events):
                    print(event)

                print("")

                print("EXPECTED:")
                print("")

                for i, event in enumerate(expected):
                    print(event)

                raise Exception("Events not correct.")

    @unittest.skipIf(_HAS_PYTHON2_UNICODE_SUPPORT is False, "Not in Python 2")
    def test__international_naming_python2(self):
        with inotify.test_support.temp_path() as path:
            inner_path = os.path.join(unicode(path), u'新增資料夾')
            os.mkdir(inner_path)

            i = inotify.adapters.Inotify()
            wd = i.add_watch(inner_path)

            with open(os.path.join(inner_path, u'filename料夾'), 'w'):
                pass

            events = self.__read_all_events(i)

            expected = [
                (inotify.adapters._INOTIFY_EVENT(wd=wd, mask=256, cookie=0, len=16), ['IN_CREATE'], inner_path, u'filename料夾'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd, mask=32, cookie=0, len=16), ['IN_OPEN'], inner_path, u'filename料夾'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd, mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], inner_path, u'filename料夾'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd, mask=16, cookie=0, len=16), ['IN_CLOSE_NOWRITE'], inner_path, u'filename料夾'),
            ]

            if events != expected:
                print("ACTUAL:")
                print("")

                for i, event in enumerate(events):
                    print(event)

                print("")

                print("EXPECTED:")
                print("")

                for i, event in enumerate(expected):
                    print(event)

                raise Exception("Events not correct.")

    def test__cycle(self):
        with inotify.test_support.temp_path() as path:
            path1 = os.path.join(path, 'aa')
            os.mkdir(path1)

            path2 = os.path.join(path, 'bb')
            os.mkdir(path2)

            i = inotify.adapters.Inotify()
            wd = i.add_watch(path1)

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
                    inotify.adapters._INOTIFY_EVENT(wd=wd, mask=256, cookie=0, len=16),
                    ['IN_CREATE'],
                    path1,
                    'seen_new_file'
                ),
                (
                    inotify.adapters._INOTIFY_EVENT(wd=wd, mask=32, cookie=0, len=16),
                    ['IN_OPEN'],
                    path1,
                    'seen_new_file'
                ),
                (
                    inotify.adapters._INOTIFY_EVENT(wd=wd, mask=8, cookie=0, len=16),
                    ['IN_CLOSE_WRITE'],
                    path1,
                    'seen_new_file'
                ),
                (
                    inotify.adapters._INOTIFY_EVENT(wd=wd, mask=512, cookie=0, len=16),
                    ['IN_DELETE'],
                    path1,
                    'seen_new_file'
                )
            ]

            if events != expected:
                print("ACTUAL:")
                print("")

                for i, event in enumerate(events):
                    print(event)

                print("")

                print("EXPECTED:")
                print("")

                for i, event in enumerate(expected):
                    print(event)

                raise Exception("Events not correct.")

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
            
            wd_path1 = get_wd(i, path1)
            wd_path2 = get_wd(i, path2)


            os.remove(os.path.join(path1, 'seen_new_file'))

            events = self.__read_all_events(i)

            expected = [
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path1, mask=256, cookie=0, len=16), ['IN_CREATE'], path1, u'seen_new_file'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path1, mask=32, cookie=0, len=16), ['IN_OPEN'], path1, u'seen_new_file'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path1, mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], path1, u'seen_new_file'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path2, mask=256, cookie=0, len=16), ['IN_CREATE'], path2, u'seen_new_file2'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path2, mask=32, cookie=0, len=16), ['IN_OPEN'], path2, u'seen_new_file2'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path2, mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], path2, u'seen_new_file2'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path1, mask=512, cookie=0, len=16), ['IN_DELETE'], path1, u'seen_new_file'),
            ]

            if events != expected:
                print("ACTUAL:")
                print("")

                for i, event in enumerate(events):
                    print(event)

                print("")

                print("EXPECTED:")
                print("")

                for i, event in enumerate(expected):
                    print(event)

                raise Exception("Events not correct.")

    def test__error_on_watch_nonexistent_folder(self):
        i = inotify.adapters.Inotify()
        with self.assertRaises(inotify.calls.InotifyError):
            i.add_watch('/dev/null/foo')

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

            time.sleep(.10)

            path2 = os.path.join(path, 'bb')
            os.mkdir(path2)

            time.sleep(.10)

            i = inotify.adapters.InotifyTree(path)

            with open('seen_new_file1', 'w'):
                pass

            time.sleep(.10)

            with open(os.path.join(path1, 'seen_new_file2'), 'w'):
                pass

            time.sleep(.10)

            with open(os.path.join(path2, 'seen_new_file3'), 'w'):
                pass

            time.sleep(.10)
            
            wd_path  = get_wd(i.inotify, path)
            wd_path1 = get_wd(i.inotify, path1)
            wd_path2 = get_wd(i.inotify, path2)

            os.remove(os.path.join(path, 'seen_new_file1'))

            time.sleep(.10)

            os.remove(os.path.join(path1, 'seen_new_file2'))

            time.sleep(.10)

            os.remove(os.path.join(path2, 'seen_new_file3'))

            time.sleep(.10)

            os.rmdir(path1)

            time.sleep(.10)

            os.rmdir(path2)

            time.sleep(.10)

            events = self.__read_all_events(i)
            events = sorted(events)
            
            expected = [
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path, mask=256, cookie=0, len=16), ['IN_CREATE'], path, 'seen_new_file1'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path, mask=32, cookie=0, len=16), ['IN_OPEN'], path, 'seen_new_file1'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path, mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], path, 'seen_new_file1'),

                (inotify.adapters._INOTIFY_EVENT(wd=wd_path1, mask=256, cookie=0, len=16), ['IN_CREATE'], path1, 'seen_new_file2'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path1, mask=32, cookie=0, len=16), ['IN_OPEN'], path1, 'seen_new_file2'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path1, mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], path1, 'seen_new_file2'),

                (inotify.adapters._INOTIFY_EVENT(wd=wd_path2, mask=256, cookie=0, len=16), ['IN_CREATE'], path2, 'seen_new_file3'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path2, mask=32, cookie=0, len=16), ['IN_OPEN'], path2, 'seen_new_file3'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path2, mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], path2, 'seen_new_file3'),

                (inotify.adapters._INOTIFY_EVENT(wd=wd_path, mask=512, cookie=0, len=16), ['IN_DELETE'], path, 'seen_new_file1'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path1, mask=512, cookie=0, len=16), ['IN_DELETE'], path1, 'seen_new_file2'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path2, mask=512, cookie=0, len=16), ['IN_DELETE'], path2, 'seen_new_file3'),

                (inotify.adapters._INOTIFY_EVENT(wd=wd_path1, mask=1024, cookie=0, len=0), ['IN_DELETE_SELF'], path1, ''),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path1, mask=32768, cookie=0, len=0), ['IN_IGNORED'], path1, ''),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path, mask=1073742336, cookie=0, len=16), ['IN_DELETE', 'IN_ISDIR'], path, 'aa'),

                (inotify.adapters._INOTIFY_EVENT(wd=wd_path2, mask=1024, cookie=0, len=0), ['IN_DELETE_SELF'], path2, ''),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path2, mask=32768, cookie=0, len=0), ['IN_IGNORED'], path2, ''),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path, mask=1073742336, cookie=0, len=16), ['IN_DELETE', 'IN_ISDIR'], path, 'bb'),
            ]

            expected = sorted(expected)

            if events != expected:
                print("ACTUAL:")
                print("")

                for i, event in enumerate(events):
                    print(event)

                print("")

                print("EXPECTED:")
                print("")

                for i, event in enumerate(expected):
                    print(event)

                raise Exception("Events not correct.")

    def test__renames(self):

        # Since we're not reading the events one at a time in a loop and
        # removing or renaming folders will flush any queued events, we have to
        # group things in order to check things first before such operations.

        with inotify.test_support.temp_path() as path:
            i = inotify.adapters.InotifyTree(path)

            old_path = os.path.join(path, 'old_folder')
            new_path = os.path.join(path, 'new_folder')

            os.mkdir(old_path)
            
            wd_path = get_wd(i.inotify, path)

            events1 = self.__read_all_events(i)

            expected = [
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path, mask=1073742080, cookie=events1[0][0].cookie, len=16), ['IN_CREATE', 'IN_ISDIR'], path, 'old_folder'),
            ]

            self.assertEqual(events1, expected)

            os.rename(old_path, new_path)

            wd_old_path = get_wd(i.inotify, old_path)

            events2 = self.__read_all_events(i)

            expected = [
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path, mask=1073741888, cookie=events2[0][0].cookie, len=16), ['IN_MOVED_FROM', 'IN_ISDIR'], path, 'old_folder'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path, mask=1073741952, cookie=events2[1][0].cookie, len=16), ['IN_MOVED_TO', 'IN_ISDIR'], path, 'new_folder'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_old_path, mask=2048, cookie=0, len=0), ['IN_MOVE_SELF'], new_path, '')
            ]

            self.assertEqual(events2, expected)


            with open(os.path.join(new_path, 'old_filename'), 'w'):
                pass

            os.rename(
                os.path.join(new_path, 'old_filename'),
                os.path.join(new_path, 'new_filename'))

            os.remove(os.path.join('new_folder', 'new_filename'))
            os.rmdir('new_folder')

            events3 = self.__read_all_events(i)

            expected = [
                (inotify.adapters._INOTIFY_EVENT(wd=wd_old_path, mask=256, cookie=0, len=16), ['IN_CREATE'], new_path, 'old_filename'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_old_path, mask=32, cookie=0, len=16), ['IN_OPEN'], new_path, 'old_filename'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_old_path, mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], new_path, 'old_filename'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_old_path, mask=64, cookie=events3[3][0].cookie, len=16), ['IN_MOVED_FROM'], new_path, 'old_filename'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_old_path, mask=128, cookie=events3[4][0].cookie, len=16), ['IN_MOVED_TO'], new_path, 'new_filename'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_old_path, mask=512, cookie=0, len=16), ['IN_DELETE'], new_path, 'new_filename'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_old_path, mask=1024, cookie=0, len=0), ['IN_DELETE_SELF'], new_path, ''),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_old_path, mask=32768, cookie=0, len=0), ['IN_IGNORED'], new_path, ''),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path, mask=1073742336, cookie=0, len=16), ['IN_DELETE', 'IN_ISDIR'], path, 'new_folder'),
            ]

            if events3 != expected:
                print("ACTUAL:")
                print("")

                for i, event in enumerate(events3):
                    print(event)

                print("")

                print("EXPECTED:")
                print("")

                for i, event in enumerate(expected):
                    print(event)

                raise Exception("Events not correct.")

    def test__automatic_new_watches_on_new_paths(self):

        # Tests that watches are actively established as new folders are
        # created.

        with inotify.test_support.temp_path() as path:
            i = inotify.adapters.InotifyTree(path)

            path1 = os.path.join(path, 'folder1')
            path2 = os.path.join(path1, 'folder2')

            os.mkdir(path1)
 
            wd_path = get_wd(i.inotify, path)

            events = self.__read_all_events(i)

            expected = [
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path, mask=1073742080, cookie=0, len=16), ['IN_CREATE', 'IN_ISDIR'], path, 'folder1'),
            ]

            self.assertEqual(events, expected)


            os.mkdir(path2)

            wd_path1 = get_wd(i.inotify, path1)

            events = self.__read_all_events(i)

            expected = [
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path1, mask=1073742080, cookie=0, len=16), ['IN_CREATE', 'IN_ISDIR'], path1, 'folder2'),
            ]

            self.assertEqual(events, expected)


            with open(os.path.join(path2,'filename'), 'w'):
                pass

            wd_path2 = get_wd(i.inotify, path2)

            events = self.__read_all_events(i)

            expected = [
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path2, mask=256, cookie=0, len=16), ['IN_CREATE'], path2, 'filename'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path2, mask=32, cookie=0, len=16), ['IN_OPEN'], path2, 'filename'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path2, mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], path2, 'filename'),
            ]

            if events != expected:
                print("ACTUAL:")
                print("")

                for i, event in enumerate(events):
                    print(event)

                print("")

                print("EXPECTED:")
                print("")

                for i, event in enumerate(expected):
                    print(event)

                raise Exception("Events not correct.")

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
                
            wd = get_wd(i.inotify, path2)

            events = self.__read_all_events(i)

            expected = [
                (inotify.adapters._INOTIFY_EVENT(wd=wd, mask=256, cookie=0, len=16), ['IN_CREATE'], path2, 'filename'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd, mask=32, cookie=0, len=16), ['IN_OPEN'], path2, 'filename'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd, mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], path2, 'filename'),
            ]

            if events != expected:
                print("ACTUAL:")
                print("")

                for i, event in enumerate(events):
                    print(event)

                print("")

                print("EXPECTED:")
                print("")

                for i, event in enumerate(expected):
                    print(event)

                raise Exception("Events not correct.")


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

            wd_path1 = get_wd(i.inotify, path1)
            wd_path2 = get_wd(i.inotify, path2)

            with open(os.path.join(path1, 'seen_new_file1'), 'w'):
                pass

            with open(os.path.join(path2, 'seen_new_file2'), 'w'):
                pass

            events = self.__read_all_events(i)

            expected = [
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path1, mask=256, cookie=0, len=16), ['IN_CREATE'], path1, 'seen_new_file1'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path1, mask=32, cookie=0, len=16), ['IN_OPEN'], path1, 'seen_new_file1'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path1, mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], path1, 'seen_new_file1'),

                (inotify.adapters._INOTIFY_EVENT(wd=wd_path2, mask=256, cookie=0, len=16), ['IN_CREATE'], path2, 'seen_new_file2'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path2, mask=32, cookie=0, len=16), ['IN_OPEN'], path2, 'seen_new_file2'),
                (inotify.adapters._INOTIFY_EVENT(wd=wd_path2, mask=8, cookie=0, len=16), ['IN_CLOSE_WRITE'], path2, 'seen_new_file2'),
            ]

            self.assertEqual(events, expected)
