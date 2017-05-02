import unittest

from pypore.core import Segment
from pypore.core import MetaSegment
from pypore.tests.segment_tests import *


class TestMetaSegment(unittest.TestCase):
    """
    Tests for :py:class:`pypore.core.MetaSegment`
    """

    def _test_attributes(self, meta_segment, sample_rate, shape, size, maximum, mean, minimum, std):
        """
        Tests that the meta_segment has the correct parameters.
        :param meta_segment: MetaSegment to be compared to other parameters.
        """
        # Test attributes are equal
        self.assertEqual(sample_rate, meta_segment.sample_rate)
        self.assertEqual(shape, meta_segment.shape)
        if shape is not None:
            self.assertEqual(len(shape), meta_segment._ndim)
        else:
            self.assertEqual(None, meta_segment._ndim)
        self.assertEqual(size, meta_segment.size)

        # Test method attributes are equal
        self.assertEqual(maximum, meta_segment.max())
        self.assertEqual(mean, meta_segment.mean())
        self.assertEqual(minimum, meta_segment.min())
        self.assertEqual(std, meta_segment.std())

    def test_from_segment(self):
        """
        Tests that Segment can be cast to a MetaSegment
        """
        array = np.random.random(100)
        s = Segment(array)

        ms = MetaSegment.from_segment(s)

        self._test_attributes(ms, sample_rate=s.sample_rate, shape=s.shape, size=s.size, maximum=s.max(),
                              mean=s.mean(), minimum=s.min(), std=s.std())

    def test_explicit_param_setting(self):
        """
        Tests that we can explicitly set the MetaSegment's parameters.
        """
        sample_rate = 1.e6
        shape = (1, 10)
        size = 10
        maximum = 99.
        minimum = 88.
        mean = 90.
        std = 3.

        ms = MetaSegment(sample_rate=sample_rate, shape=shape, size=size, maximum=maximum, minimum=minimum, mean=mean,
                         std=std)

        self._test_attributes(ms, sample_rate=sample_rate, shape=shape, size=size, maximum=maximum,
                              mean=mean, minimum=minimum, std=std)

    def test_attributes_can_be_none(self):
        """
        Attributes are allowed to be None.
        """

        ms = MetaSegment()

        self._test_attributes(ms, sample_rate=None, shape=None, size=None, maximum=None,
                              mean=None, minimum=None, std=None)


class TestSegment(unittest.TestCase, SegmentTests):
    """
    Tests for Segment
    """

    SEGMENT_CLASS = Segment

    def setUp(self):
        self.default_test_data = []

        for data in [np.random.random(100), np.zeros(500), [1, 2, 3, 4, 5, 6]]:
            self.default_test_data.append(SegmentTestData(data, sample_rate=1.e6))

        # add one element data with no sample rate
        data = np.random.random(1)
        self.default_test_data.append(SegmentTestData(data))

        # add multichannel data

    def test_slicing_numpy_array(self):
        """
        Tests that slicing a Segment holding numpy array data works well.
        """
        array = np.random.random(100)

        s = Segment(array)

        # Regular slices
        np.testing.assert_array_equal(array, s)
        np.testing.assert_array_equal(array[:], s[:])
        np.testing.assert_array_equal(array[:19], s[:19])
        np.testing.assert_array_equal(array[55:], s[55:])
        np.testing.assert_array_equal(array[1:5], s[1:5])
        np.testing.assert_array_equal(array[5:100], s[5:100])

        # steps
        np.testing.assert_array_equal(array[::3], s[::3])
        np.testing.assert_array_equal(array[::-3], s[::-3])

        # Negative indices
        np.testing.assert_array_equal(array[-10:], s[-10:])
        np.testing.assert_array_equal(array[:-10], s[:-10])
        np.testing.assert_array_equal(array[-95:-5], s[-95:-5])

        # Slicing slices
        np.testing.assert_array_equal(array[:][:], s[:][:])
        np.testing.assert_array_equal(array[:19][:19], s[:19][:19])
        np.testing.assert_array_equal(array[1:15][:10:2], s[1:15][:10:2])
        np.testing.assert_array_equal(array[-1:][:], s[-1:][:])
        np.testing.assert_array_equal(array[:][:][:], s[:][:][:])

    def test_list(self):
        """
        Tests that we can pass in a list to Segment.
        """
        l = [1, 2, 3, 4, 5, 6]

        s = Segment(l)

        self.assertEqual(len(l), len(s))
        self.assertEqual(len(l), s.size)

    def test_sample_rate(self):
        """
        Tests that the sample rate is a named argument. Tests that sample_rate can be None.
        """
        # Test that sample_rate is initialized to zero.
        array = np.random.random(100)

        s = Segment(array)

        self.assertEqual(s.sample_rate, 0.0, "Segment without a sample rate should have the sample rate set to zero.")

        # Test setting the sample_rate.
        sample_rate = 1.2343e9
        s2 = Segment(array, sample_rate=sample_rate)

        self.assertEqual(sample_rate, s2.sample_rate, "Segment's sample_rate incorrect. Should be {0}. Was {"
                                                      "1}".format(sample_rate, s2.sample_rate))
