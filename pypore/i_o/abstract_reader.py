from pypore.core import Segment


class AbstractReader(Segment):
    """
    This is an abstract class showing the methods that Reader subclasses must override.

    Readers are subclasses of :py:class:`pypore.core.Segment` where the data is read from a file.

    To subclass a Reader, see the methods in this class as well as :py:class:`pypore.core.Segment` for examples.
    """
    filename = None
    directory = None

    # extra fields specific to readers should be accessible from
    metadata = None

    # _chunk_size can be used by subclasses when lazy loading data
    # default is ~100kB of 64 bit floating points
    # units are datapoints
    _chunk_size = 12500

    @property
    def chunk_size(self):
        return self._chunk_size

    def __init__(self, *args, **kwargs):
        """
        Opens a data file, reads relevant parameters, and returns then open file and parameters.

        :param StringType filename: Filename to open and read parameters.

        If there was an error opening the files, params will have 'error' key with string description.
        """
        raise NotImplementedError

    def close(self):
        """close()

        Closes the file and the reader.
        """
        raise NotImplementedError
