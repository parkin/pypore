from pypore.i_o.abstract_reader import AbstractReader

import unittest


class TestAbstractReader(unittest.TestCase):
    def test_not_implemented(self):
        """
        Tests that we cannot instantiate AbstractReader
        :return:
        """
        self.assertRaises(NotImplementedError, AbstractReader, 'hi.txt')

    def test_close_raises(self):
        """
        Tests that the close method exists and raises NotImplementedError.
        """
        self.assertRaises(NotImplementedError, AbstractReader.close, AbstractReader.__new__(AbstractReader))
