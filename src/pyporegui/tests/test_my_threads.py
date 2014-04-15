import os
import unittest

from PySide import QtGui
from pypore.tests.util import _test_file_manager

from pyporegui.my_threads import AnalyzeDataThread
import pypore.sampledata.testing_files as tf
from pypore.event_finder import Parameters

# This test class needs a QApplication instance
if QtGui.qApp is None:
    QtGui.QApplication([])

DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class TestAnalyzeDataThread(unittest.TestCase):
    @_test_file_manager(DIRECTORY)
    def test_one_file_with_events(self, filename):
        """
        Tests that events are found and event databases are saved.
        """
        test_data_file_names = tf.get_all_file_names()

        test_file = tf.get_abs_path('chimera_1event.log')
        analyze_thread = AnalyzeDataThread([test_file], Parameters(), debug=True, save_file_names=[filename])
        analyze_thread.start()

        # wait until the thread has finished
        analyze_thread.wait()

        self.assertTrue(os.path.exists(filename))

