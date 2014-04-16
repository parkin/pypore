import numpy as np


class ReaderTests(object):
    """
    Other test classes for readers should inherit this class in addition to unittest.TestCase.

    Subclasses **must** use multi-inheritance and also inherit from :py:class:`unittest.TestCase`.

    The subclass **must** have a field 'reader_class' that is a subclass of
    :py:class:`AbstractReader <pypore.i_o.abstract_reader.AbstractReader>`. For example::

        self.reader_class = ChimeraReader

    The subclasses also **must** override the following methods:

    #. :py:func:`help_scaling`
    #. :py:func:`help_scaling_decimated`
    #. :py:func:`help_get_all_data_returns_to_beginning`

    """
    reader_class = None

    def help_get_all_data_returns_to_beginning(self):
        """
        Should be overridden by a subclass and return the following.

        :returns: Filename
        """
        raise NotImplementedError('Inheritors should override this method.')

    def test_scaling(self):
        """
        Tests that the data is scaled correctly, from a known test file.
        """
        file_names, means_should_be, std_devs_should_be = self.help_scaling()

        for i, filename in enumerate(file_names):
            mean_should_be = means_should_be[i]
            std_dev_should_be = std_devs_should_be[i]

            reader = self.reader_class(filename)

            data = reader.get_all_data()[0]
            reader.close()

            mean = np.mean(data)

            mean_diff = abs((mean - mean_should_be) / mean_should_be)
            self.assertLessEqual(mean_diff, 0.05,
                                 "Data mean in '{0}' scaled wrong. "
                                 "Should be {1}, got {2}.".format(filename, mean_should_be, mean))

            std_dev = np.std(data)

            std_diff = abs((std_dev - std_dev_should_be) / std_dev_should_be)
            self.assertLessEqual(std_diff, 0.05,
                                 "Baseline in '{0}' scaled wrong. "
                                 "Should be {1}, got {2}.".format(filename, std_dev_should_be, std_dev))

    def help_scaling(self):
        """
        Subclasses should override this method and return the following, in the following order.
        :returns: The following, in order:

        #. list of file names of the test files.
        #. list of known means of the data in the test files to check against the reader_class.
        #. list of known standard deviations of the data to check against the reader_class.

        """
        raise NotImplementedError('Inheritors should override this method.')

    def test_scaling_decimated(self):
        """
        Tests that the decimated data is scaled the same as the un-decimated data.
        """
        file_names = self.help_scaling_decimated()

        for filename in file_names:
            reader = self.reader_class(filename)

            data = reader.get_all_data()[0]
            data_decimated = reader.get_all_data(decimate=True)[0]
            reader.close()

            mean = np.mean(data)
            mean_decimated = np.mean(data_decimated)

            mean_percent_diff = abs((mean - mean_decimated) / mean)
            self.assertLessEqual(mean_percent_diff, 0.05,
                                 "Decimated mean in '{0}' scaled wrong. "
                                 "Should be {1}, got {2}.".format(filename, mean, mean_decimated))

    def help_scaling_decimated(self):
        """
        Subclasses should override this method and return the filename used to check that the decimated and un-decimated
        data :py:func:`get_all_data <pypore.i_o.abstract_reader.AbstractReader.get_all_data>`.

        :returns: filename for testing decimated scaling.
        """
        raise NotImplementedError('Inheritors should override this method.')
