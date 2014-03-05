"""

"""

import unittest
import os

from pypore.fileConverter import convert_file
from pypore.dataFileOpener import open_data


class TestFileConverter(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_convert_file(self):
        filename = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(filename, 'testDataFiles', 'chimera_1event.log')

        output_filename = "out.h5"

        output_file = convert_file(filename, output_filename=output_filename)

        # Test that we can set the output filename
        self.assertEqual(output_file, output_filename, "output_filename not correct")



        os.remove(output_file)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

