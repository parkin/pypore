import numpy as np


class ReaderTests(object):
    """
    Other test classes for readers should inherit this class in addition to unittest.TestCase.

    Subclasses **must** use multi-inheritance and also inherit from :py:class:`unittest.TestCase`.

    The subclass **must** have a field 'reader_class' that is a subclass of
    :py:class:`AbstractReader <pypore.i_o.abstract_reader.AbstractReader>`. For example::

        self.reader_class = ChimeraReader

    The subclasses also **must** override the following methods:

    #. :py:func:`help_test_scaling`
    #. :py:func:`help_test_scaling_decimated`

    """
    reader_class = None

    def test_scaling(self):
        """
        Tests that the data is scaled correctly, from a known test file.
        """
        filename, mean_should_be, mean_places, std_dev_should_be, std_dev_places = self.help_test_scaling()

        reader = self.reader_class(filename)

        data = reader.get_all_data()[0]
        reader.close()

        mean = np.mean(data)

        self.assertAlmostEqual(mean, mean_should_be, mean_places,
                               "Data mean scaled wrong. Should be {0}, got {1}.".format(mean_should_be, mean))

        std_dev = np.std(data)

        self.assertAlmostEqual(std_dev, std_dev_should_be, std_dev_places,
                               "Baseline scaled wrong. Should be {0}, got {1}.".format(std_dev_should_be, std_dev))

    def help_test_scaling(self):
        """
        Subclasses should override this method and return the following, in the following order.
        :returns: The following, in order:

        #. filename of the test file.
        #. known mean of the data in the test file to check against the reader_class.
        #. number of decimal places to compare the mean.
        #. known standard deviation of the data to check against the reader_class.
        #. number of decimal places to compare the standard deviation.

        """
        raise NotImplementedError

    def test_scaling_decimated(self):
        """
        Tests that the decimated data is scaled the same as the un-decimated data.
        """
        filename = self.help_test_scaling_decimated()

        reader = self.reader_class(filename)

        data = reader.get_all_data()[0]
        data_decimated = reader.get_all_data(decimate=True)[0]
        reader.close()

        mean = np.mean(data)
        mean_decimated = np.mean(data_decimated)

        mean_percent_diff = abs((mean - mean_decimated) / mean)
        self.assertLessEqual(mean_percent_diff, 0.05,
                             "Decimated mean scaled wrong. Should be {0}, got {1}.".format(mean, mean_decimated))

    def help_test_scaling_decimated(self):
        """
        Subclasses should override this method and return the filename used to check that the decimated and un-decimated
        data :py:func:`get_all_data <pypore.i_o.abstract_reader.AbstractReader.get_all_data>`.

        :returns: filename for testing decimated scaling.
        """
        raise NotImplementedError
