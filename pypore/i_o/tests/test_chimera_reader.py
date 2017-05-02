"""
"""
import unittest

from pypore.tests.segment_tests import SegmentTestData
from pypore.i_o.chimera_reader import ChimeraReader
from pypore.i_o.tests.reader_tests import ReaderTests
import pypore.sampledata.testing_files as tf


class TestChimeraReader(unittest.TestCase, ReaderTests):
    SEGMENT_CLASS = ChimeraReader

    default_test_data = [
        SegmentTestData(tf.get_abs_path('chimera_small.log'), maximum=1.8157181e-08, mean=1.7765718e-08,
                        minimum=1.7157802e-08, shape=(10,), size=10, std=3.5689698e-10, sample_rate=4166666.6666666665),
        SegmentTestData(tf.get_abs_path('spheres_20140114_154938_beginning.log'), maximum=1.1914651e-08,
                        mean=7.5760553e-09, minimum=2.7252511e-09, shape=(102400,), size=102400, std=1.1544473e-09,
                        sample_rate=6250000.0)]

    def test_constructor_no_mat_spec(self):
        """
        Tests that an IOError is raised when no .mat spec file is next to the .log file.
        """
        test_no_mat_chimera_files = tf.get_abs_path('chimera_empty.log')
        for filename in test_no_mat_chimera_files:
            self.assertRaises(IOError, ChimeraReader, filename)
