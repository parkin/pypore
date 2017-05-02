import unittest

import pypore.sampledata.testing_files as tf
import pypore
from pypore.i_o.chimera_reader import ChimeraReader
from pypore.i_o.heka_reader import HekaReader


class TestInit(unittest.TestCase):
    def test_open_file_from_extension(self):
        """
        Tests that the file extension is parsed correctly and the correct Reader is opened.
        """
        # Chimera file
        filename = tf.get_abs_path('spheres_20140114_154938_beginning.log')
        f = pypore.open_file(filename)
        self.assertTrue(isinstance(f, ChimeraReader))
        f.close()

        # Heka file
        filename = tf.get_abs_path('heka_1.5s_mean5.32p_std2.76p.hkd')
        f = pypore.open_file(filename)
        self.assertTrue(isinstance(f, HekaReader))
        f.close()

    def test_opening_bad_extension_raises(self):
        """
        Tests that opening a file based on extension when a reader doesn't exist for that extension will result in a
        ValueError.
        """
        self.assertRaises(ValueError, pypore.open_file, 'this_extension_does_not_exist.rollercoaster')

    def test_open_file_with_reader_class(self):
        """
        Tests that we can pass in a Reader class to open the file with.
        """
        # Chimera file
        filename = tf.get_abs_path('spheres_20140114_154938_beginning.log')
        f = pypore.open_file(filename, ChimeraReader)
        f.close()
        self.assertTrue(isinstance(f, ChimeraReader))

        # Heka file
        filename = tf.get_abs_path('heka_1.5s_mean5.32p_std2.76p.hkd')
        f = pypore.open_file(filename)
        f.close()
        self.assertTrue(isinstance(f, HekaReader))

        # Test that passing the wrong Reader results in an error
        # Aka that the reader_class we pass in is actually used.
        filename = tf.get_abs_path('heka_1.5s_mean5.32p_std2.76p.hkd')
        # Heka files should produce an error when being ready by ChimeraReader.
        self.assertRaises(IOError, pypore.open_file, filename, ChimeraReader)

