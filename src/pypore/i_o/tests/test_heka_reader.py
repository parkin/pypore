import unittest

from pypore.i_o.heka_reader import HekaReader
from pypore.i_o.tests.reader_tests import ReaderTests
import pypore.sampledata.testing_files as tf


class TestHekaReader(unittest.TestCase, ReaderTests):
    reader_class = HekaReader

    default_test_data_files = [tf.get_abs_path('heka_1.5s_mean5.32p_std2.76p.hkd')]

    def help_scaling(self):
        filename = tf.get_abs_path('heka_1.5s_mean5.32p_std2.76p.hkd')
        mean = 5.32e-12
        std_dev = 2.76e-12
        return [filename], [mean], [std_dev]

    @unittest.skip("Test file is too short for decimated and un-decimated means to be equal enough.")
    def test_scaling_decimated(self):
        super(TestHekaReader, self).test_scaling_decimated()

