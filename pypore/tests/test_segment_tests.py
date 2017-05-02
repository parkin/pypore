import unittest

import numpy as np

from pypore.tests.segment_tests import SegmentTestData


class TestSegmentTestData(unittest.TestCase):
    """
    Tests for the SegmentTestData data class.
    """

    def _assert_fields_equal_to_data(self, segmentTestData, data):
        """
        Asserts that the following fields of segmentTestData are equal to the value computed by numpy.

            #. max
            #. mean
            #. min
            #. shape
            #. size
            #. std

        :param segmentTestData:
        :param data: Underlying data in segmentTestData
        :return:
        """
        self.assertEqual(segmentTestData.max, np.max(data))
        self.assertEqual(segmentTestData.mean, np.mean(data))
        self.assertEqual(segmentTestData.min, np.min(data))
        self.assertEqual(segmentTestData.shape, np.shape(data))
        self.assertEqual(segmentTestData.size, np.size(data))
        self.assertEqual(segmentTestData.std, np.std(data))

    def test_default_constructor_args(self):
        """
        Test that the constructor arguments are set correctly.
        """
        data = np.random.random(10)

        s = SegmentTestData(data)

        self._assert_fields_equal_to_data(s, data)

        np.testing.assert_array_equal(s.data, data)

    def test_default_constructor_args_multichannel(self):
        """
        Tests that the fields are set correctly in the constructor.
        """
        data = np.random.random((5, 5))

        s = SegmentTestData(data)

        self._assert_fields_equal_to_data(s, data)

        np.testing.assert_array_equal(s.data, data)

    def test_setting_constructor_args(self):
        """
        Tests that we can set the constructor arguments
        :return:
        """

        maximum = 1.
        mean = 2.
        minimum = 3.
        shape = (4, 2)
        size = 8
        std = 5.

        data = 'nonexisting_test_file.dat'

        s = SegmentTestData(data, maximum=maximum, mean=mean, minimum=minimum, shape=shape, size=size, std=std)

        self.assertEqual(s.max, maximum)
        self.assertEqual(s.mean, mean)
        self.assertEqual(s.min, minimum)
        self.assertEqual(s.shape, shape)
        self.assertEqual(s.size, size)
        self.assertEqual(s.std, std)

        self.assertEqual(s.data, data)
