import unittest

from pypore.util import *


class _ItemRet(object):
    def __getitem__(self, item):
        return item


class TestUtil(unittest.TestCase):
    def test_process_range(self):
        length = 100

        # Normal
        self.assertEqual(process_range(None, None, None, length), (0, length, 1))
        self.assertEqual(process_range(0, None, None, length), (0, length, 1))
        self.assertEqual(process_range(1, None, None, length), (1, length, 1))
        self.assertEqual(process_range(None, None, 2, length), (0, length, 2))

        # out of bounds
        self.assertEqual(process_range(None, 1000000, None, length), (0, length, 1))

        # Negatives
        self.assertEqual(process_range(-1, None, None, length), (length - 1, length, 1))
        self.assertEqual(process_range(-10, None, None, length), (length - 10, length, 1))
        self.assertEqual(process_range(None, -1, None, length), (0, length - 1, 1))

        # Negatives out of bounds
        self.assertEqual(process_range(-5000, None, None, length), (0, length, 1))
        self.assertEqual(process_range(None, -10000, None, length), (0, 0, 1))

        # Negatives steps
        self.assertEqual(process_range(None, None, -1, length), (length - 1, -1, -1))
        self.assertEqual(process_range(5, 2, -1, 10), (5, 2, -1))
        self.assertEqual(process_range(-1, -4, -1, 10), (9, 6, -1))
        self.assertEqual(process_range(-1, -100, -1, 10), (9, -1, -1))
        self.assertEqual(process_range(999, None, -1, 10), (9, -1, -1))

        # Errors
        self.assertRaises(ValueError, process_range, None, None, 0, length)

    def test_is_index(self):
        """
        Tests that the is_index method only accepts index like values.
        """

        self.assertTrue(is_index(1))
        self.assertTrue(is_index(int(3923492)))
        if sys.version_info < (3, 0):
            self.assertTrue(is_index(long(34843983214892)))
        self.assertTrue(is_index(np.array([1])[0]))

        self.assertFalse(is_index("h"))
        self.assertFalse(is_index('h'))
        self.assertFalse(is_index(5.0))
        self.assertFalse(is_index(float(5)))
        self.assertFalse(is_index(0.5))
        self.assertFalse(is_index(self))
        self.assertFalse(is_index(open))

    def test_interpret_indexing_normal_usage(self):
        item_ret = _ItemRet()

        # # Test normal usage

        args = []  # will contain arguments to interpret_indexing
        expected_results = []  # will contain expected results from interpret_indexing

        # Test selecting single item from single row
        args.append((item_ret[0], (1000,)))
        expected_results.append((
            np.array([0], dtype=np.integer), np.array([1], dtype=np.integer),
            np.array([1], dtype=np.integer),
            (1,)))

        # Test selecting single item from single row
        args.append((item_ret[:], (1000,)))
        expected_results.append((
            np.array([0], dtype=np.integer), np.array([1000], dtype=np.integer),
            np.array([1], dtype=np.integer),
            (1000,)))

        # Test selecting single row
        args.append((item_ret[0], (2, 1000)))
        expected_results.append((
            np.array([0, 0], dtype=np.integer), np.array([1, 1000], dtype=np.integer),
            np.array([1, 1], dtype=np.integer),
            (1, 1000)))

        # Test selecting single row
        args.append((item_ret[1], (2, 1000)))
        expected_results.append((
            np.array([1, 0], dtype=np.integer), np.array([2, 1000], dtype=np.integer),
            np.array([1, 1], dtype=np.integer),
            (1, 1000)))

        # Test selecting single row with negative index
        args.append((item_ret[-1], (2, 1000)))
        expected_results.append((
            np.array([1, 0], dtype=np.integer), np.array([2, 1000], dtype=np.integer),
            np.array([1, 1], dtype=np.integer),
            (1, 1000)))

        # Test selecting single row with negative index
        args.append((item_ret[-5], (10, 1000)))
        expected_results.append((
            np.array([5, 0], dtype=np.integer), np.array([6, 1000], dtype=np.integer),
            np.array([1, 1], dtype=np.integer),
            (1, 1000)))

        # Test selecting single number
        args.append((item_ret[1, 1], (2, 1000)))
        expected_results.append((
            np.array([1, 1], dtype=np.integer), np.array([2, 2], dtype=np.integer), np.array([1, 1], dtype=np.integer),
            (1, 1)))

        args.append((item_ret[:, :], (2, 1000)))
        expected_results.append((
            np.array([0, 0], dtype=np.integer), np.array([2, 1000], dtype=np.integer),
            np.array([1, 1], dtype=np.integer),
            (2, 1000)))

        args.append((item_ret[1:5, 1], (2, 1000)))
        expected_results.append((
            np.array([1, 1], dtype=np.integer), np.array([2, 2], dtype=np.integer), np.array([1, 1], dtype=np.integer),
            (1, 1)))

        args.append((item_ret[1, 0:10], (2, 1000)))
        expected_results.append((
            np.array([1, 0], dtype=np.integer), np.array([2, 10], dtype=np.integer), np.array([1, 1], dtype=np.integer),
            (1, 10)))

        args.append((item_ret[1, 1], (2, 1000)))
        expected_results.append((
            np.array([1, 1], dtype=np.integer), np.array([2, 2], dtype=np.integer), np.array([1, 1], dtype=np.integer),
            (1, 1)))

        # Test each set of arguments against the expected result
        for i, arg in enumerate(args):
            result = interpret_indexing(*arg)
            expected_result = expected_results[i]

            # make sure the starts, stops, steps arrays are equal
            for j in range(3):
                np.testing.assert_array_equal(result[j], expected_result[j], "Arrays at index {0} not equal.".format(j))

            # make sure the final shape is correct
            self.assertEqual(result[3], expected_result[3])

    def test_interpret_indexing_errors(self):
        item_ret = _ItemRet()

        # # Test errors
        # Test index errors
        self.assertRaises(IndexError, interpret_indexing, item_ret[100], (1, 3))
        self.assertRaises(IndexError, interpret_indexing, item_ret[1, 100], (100, 3))
        self.assertRaises(IndexError, interpret_indexing, item_ret[0, 0, 500], (1, 3, 1))

        # Test invalid slices
        self.assertRaises(IndexError, interpret_indexing, item_ret[1, 100], (100,))
        self.assertRaises(IndexError, interpret_indexing, item_ret[0, 0, 500], (1, 3))

        # Test for non indexes
        self.assertRaises(TypeError, interpret_indexing, item_ret['a'], (100,))


class TestSliceCombine(unittest.TestCase):
    def test_slicing_1d_2_slices(self):
        """
        Tests 2 combined slicing on 1D data for a bunch of different slices.
        """
        # Make a 1D dataset
        x = np.arange(5)
        length = len(x)

        # Test indices and steps
        indices = [None, -6, -2, -1, 0, 1, 3, 6]
        steps = [-6, -3, -1, 1, 2, 6]
        indices_l = len(indices)
        steps_l = len(steps)

        count = 0
        # 2 tests per loop
        total = 2 * indices_l ** 4 * steps_l ** 2
        for i in range(indices_l):
            for j in range(indices_l):
                for k in range(steps_l):
                    for q in range(indices_l):
                        for r in range(indices_l):
                            for s in range(steps_l):
                                slice1 = slice(indices[i], indices[j], steps[k])
                                slice2 = slice(indices[q], indices[r], steps[s])

                                combined = slice_combine(length, slice1, slice2)
                                np.testing.assert_array_equal(x[slice1][slice2], x[combined],
                                                              err_msg="For 1D, slice1: {0},"
                                                                      "\tslice2: {1},\tcombined: {2}\tPROGRESS: {"
                                                                      "3}/{4} ({5:.0f}%)".format(slice1, slice2,
                                                                                                 combined, count,
                                                                                                 total,
                                                                                                 float(count) / total))

                                count += 1

    def test_slicing_2d_2_slices(self):
        """
        Tests 2 combined slicing on 2D data for a bunch of different slices.
        """
        # Make a 1D dataset
        x = np.arange(10)
        x = x.reshape((5, 2))
        length = len(x)

        # Test indices and steps
        indices = [None, -6, -2, -1, 0, 1, 3, 6]
        steps = [-6, -3, -1, 1, 2, 6]
        indices_l = len(indices)
        steps_l = len(steps)

        count = 0
        # 2 tests per loop
        total = 2 * indices_l ** 4 * steps_l ** 2
        for i in range(indices_l):
            for j in range(indices_l):
                for k in range(steps_l):
                    for q in range(indices_l):
                        for r in range(indices_l):
                            for s in range(steps_l):
                                slice1 = slice(indices[i], indices[j], steps[k])
                                slice2 = slice(indices[q], indices[r], steps[s])

                                combined = slice_combine(length, slice1, slice2)
                                np.testing.assert_array_equal(x[slice1][slice2], x[combined],
                                                              err_msg="For 2D, slice1: {0},"
                                                                      "\tslice2: {1},\tcombined: {2}\tPROGRESS: {"
                                                                      "3}/{4} ({5:.0f}%)".format(slice1, slice2,
                                                                                                 combined, count,
                                                                                                 total,
                                                                                                 float(count) / total))

                                count += 1

    def test_three_slices(self):
        """
        Test that we can pass in three slices and it still works.
        """
        x = np.arange(10)
        length = len(x)

        slice1 = slice(0, 4, 2)
        slice2 = slice(None, None, -1)
        slice3 = slice(1, None, 1)

        combined = slice_combine(length, slice1, slice2, slice3)

        np.testing.assert_array_equal(x[slice1][slice2][slice3], x[combined], err_msg="Three slices failed.")

    def test_one_slice(self):
        """
        Tests that passing in one slice returns it.
        """
        x = np.arange(10)
        length = len(x)

        slice1 = slice(0, 4, 2)

        combined = slice_combine(length, slice1)

        np.testing.assert_array_equal(x[slice1], x[combined], err_msg="Three slices failed.")

    def test_no_slices_returns_empty_slice(self):
        """
        Tests that passing in no slices returns an empty slice.
        """
        combined = slice_combine(10)

        self.assertEqual(combined.start, 0)
        self.assertEqual(combined.stop, 0)
        self.assertEqual(combined.step, 1)


class TestGetSliceLength(unittest.TestCase):
    def test_regular_slices(self):
        x = np.arange(100)

        s = slice(0, None, 1)
        l = get_slice_length(len(x), s)
        self.assertEqual(l, len(x[s]))

        s = slice(None, None, -1)
        l = get_slice_length(len(x), s)
        self.assertEqual(l, len(x[s]))

        s = slice(10, 98, 3)
        l = get_slice_length(len(x), s)
        self.assertEqual(l, len(x[s]))

    def test_zero_length(self):
        x = np.arange(100)

        s = slice(10, 10, 3)
        l = get_slice_length(len(x), s)
        self.assertEqual(l, len(x[s]))

        s = slice(10, -10, 3)
        l = get_slice_length(len(x), s)
        self.assertEqual(l, len(x[s]))