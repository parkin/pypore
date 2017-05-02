import os
import unittest

import pypore.sampledata.testing_files as tf

abs_path = os.path.abspath(__file__)
abs_dir = os.path.dirname(abs_path)

TEST_FILES_PATH = os.path.abspath(os.path.join(abs_dir, '..', 'testDataFiles'))


class TestGetAbsPath(unittest.TestCase):
    def test_correct_paths(self):
        """
        Tests that the returned files are correct.
        """
        full_names = tf.get_all_file_names(with_path=True)
        short_names = tf.get_all_file_names(with_path=False)

        for i, short_name in enumerate(short_names):
            abs_path = tf.get_abs_path(short_name)
            self.assertEqual(full_names[i], abs_path,
                             msg="Absolute path not correct.\nShould be '{0}'.\nWas '{1}'.".format(full_names[i],
                                                                                                   abs_path))

    def test_not_exists_raises(self):
        """
        Test that an exception is raised if the filename is not present.
        """
        self.assertRaises(tf.TestFileDoesntExistError, tf.get_abs_path, 'blahblahblahblah.blahblahblah')


class TestGetAllFileNames(unittest.TestCase):
    def test_with_path(self):
        """
        Tests that getting all of the file names returns the correct info.
        """
        file_names_should_be = []

        for (dir_path, dir_names, file_names) in os.walk(TEST_FILES_PATH):
            for i, filename in enumerate(file_names):
                file_names[i] = os.path.join(dir_path, filename)
            file_names_should_be.extend(file_names)

        file_names = tf.get_all_file_names()

        # Currently there are 13 files in the folder.
        self.assertTrue(len(file_names), 13)
        self.assertEqual(sorted(file_names), sorted(file_names_should_be),
                         msg="Returned incorrect file names.\nShould"
                             " be {0}.\nWas {1}.".format(file_names_should_be, file_names))

        # Test that the file_names returned include their paths
        # Check the file 'chimera_small' is there
        is_chimera_small = False
        for filename in file_names:
            self.assertTrue('pypore' in filename and 'sampledata' in filename and 'testDataFiles' in filename,
                            msg="Filename should include path."
                                " Was '{0}'.".format(filename))
            if 'chimera_small.log' in filename:
                is_chimera_small = True

        self.assertTrue(is_chimera_small, msg="File {0} was not found, but was expected.".format('chimera_small.log'))

        file_names2 = tf.get_all_file_names(with_path=True)
        # Check we can pass with_path as an argument, and that True is default.
        self.assertEqual(sorted(file_names), sorted(file_names2))

    def test_no_path(self):
        """
        Tests that we can get all of the file names
        """
        file_names_should_be = []

        for (dir_path, dir_names, file_names) in os.walk(TEST_FILES_PATH):
            file_names_should_be.extend(file_names)

        file_names = tf.get_all_file_names(with_path=False)

        # Currently there are 13 files in the folder.
        self.assertTrue(len(file_names), 13)
        self.assertEqual(sorted(file_names), sorted(file_names_should_be),
                         msg="Returned incorrect file names.\nShould"
                             " be {0}.\nWas {1}.".format(file_names_should_be, file_names))

        # Test that the file_names returned do NOT include their paths
        # Check the file 'chimera_small' is there
        is_chimera_small = False
        for filename in file_names:
            self.assertTrue('sampledata' not in filename and 'testDataFiles' not in filename,
                            msg="Filename should include path."
                                " Was '{0}'.".format(filename))
            if 'chimera_small.log' == filename:
                is_chimera_small = True

        self.assertTrue(is_chimera_small, msg="File {0} was not found, but was expected.".format('chimera_small.log'))

    def test_sorted(self):
        """
        Make sure the list returned is sorted.
        """
        file_names_should_be = []

        for (dir_path, dir_names, file_names) in os.walk(TEST_FILES_PATH):
            file_names_should_be.extend(file_names)

        file_names = tf.get_all_file_names(with_path=False)

        self.assertEqual(file_names, sorted(file_names_should_be),
                         msg="List not sorted.\nShould"
                             " be {0}.\nWas {1}.".format(file_names_should_be, file_names))
