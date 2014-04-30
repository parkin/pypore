import unittest

from pypore.strategies.absolute_change_threshold_strategy import AbsoluteChangeThresholdStrategy


class TestAbsoluteChangeThresholdStrategy(unittest.TestCase):
    def test_compute_starting_threshold(self):
        """
        Test that the starting and ending thresholds do not depend on the baseline or variance.
        """
        start_changes = [-1.e9, -1, -1.e-9, 0., 1, 1.e-9, 1.e9]
        end_changes = [-1.e9, -1, -1.e-9, 0., 1, 1.e-9, 1.e9]
        baselines = [-1.e9, -1., -1.e-9, 0., 1, 1.e-9, 1.e9]
        variances = [-1.e9, -1., -1.e-9, 0., 1, 1.e-9, 1.e9]
        for i in xrange(len(start_changes)):
            strategy = AbsoluteChangeThresholdStrategy(start_changes[i], end_changes[i])

            for j in xrange(len(variances)):
                start_thresh = strategy.compute_starting_threshold(baselines[j], variances[j])
                end_thresh = strategy.compute_ending_threshold(baselines[j], variances[j])

                self.assertEqual(start_thresh, start_changes[i],
                                 "Unexpected starting threshold. Should be {0}, was {1}.".format(start_changes[i],
                                                                                                 start_thresh))
                self.assertEqual(end_thresh, end_changes[i],
                                 "Unexpected ending threshold. Should be {0}, was {1}.".format(end_changes[i],
                                                                                               end_thresh))

