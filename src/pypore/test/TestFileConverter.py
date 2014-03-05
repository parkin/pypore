"""

"""

import unittest
import os
from pypore.dataFile import DataFile

from pypore.fileConverter import convert_file


class TestFileConverter(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_convert_file_set_output_filename(self):
        filename = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(filename, 'testDataFiles', 'chimera_1event.log')

        output_filename = "out.h5"

        output_file = convert_file(filename, output_filename=output_filename)

        # Test that we can set the output filename
        self.assertEqual(output_file, output_filename, "output_filename not correct")

        os.remove(output_file)

    def test_convert_file_matrix_equality(self):
        filename = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(filename, 'testDataFiles', 'chimera_1event.log')

        output_filename = "out.h5"

        output_file = convert_file(filename, output_filename=output_filename)

        # open the output_file
        data_file = DataFile(output_file)



        pass


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

