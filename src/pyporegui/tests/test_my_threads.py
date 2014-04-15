import unittest

from PySide import QtGui

# This test class needs a QApplication instance
if QtGui.qApp is None:
    QtGui.QApplication([])


class TestAnalyzeDataThread(unittest.TestCase):
    @unittest.skip(reason="Unimplemented")
    def test_one_file_with_events(self):
        """
        Tests that events are found and event databases are saved.
        """
        pass
