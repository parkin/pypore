import numpy as np

from pypore.tests.segment_tests import SegmentTests


class ReaderTests(SegmentTests):
    """
    Other test classes for readers should inherit this class in addition to unittest.TestCase.

    See :py:class:`pypore.tests.segment_tests.SegmentTests` for further details.
    """

    def test_non_existing_file_raises(self):
        self.assertRaises(IOError, self.SEGMENT_CLASS, 'this_file_does_not_exist.nope')

    def test_sample_rate(self):
        """
        Tests that the sample rate is initialized properly.
        :return:
        """
        for test_data in self.default_test_data:
            reader = self.SEGMENT_CLASS(test_data.data)

            sample_rate = reader.sample_rate
            sample_rate_diff = np.abs(sample_rate - test_data.sample_rate) / test_data.sample_rate
            reader.close()

            self.assertTrue(sample_rate_diff <= 0.05,
                            "Sample rate read wrong from {0}. Should be {1}, got {2}.".format(test_data.data,
                                                                                              test_data.sample_rate,
                                                                                              sample_rate))

    def test_close(self):
        """
        Tests that subclasses of AbstractReader have implemented close.
        """
        reader = self.SEGMENT_CLASS(self.default_test_data[0].data)
        reader.close()