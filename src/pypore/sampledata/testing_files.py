"""
Functions that return file names of data files used for testing.
"""
import os


dir_name = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_FOLDER = 'testDataFiles'
TEST_DATA_FOLDER_PATH = os.path.join(dir_name, TEST_DATA_FOLDER)


class TestFileDoesntExistError(Exception):
    pass


def get_all_file_names(with_path=True):
    """
    :param bool with_path: Whether the returned file names should include their absolute paths. Default is True.
    :returns: A list of all of the file names in the testDataFiles directory.
    """
    ret_file_names = []

    for (dir_path, dir_names, file_names) in os.walk(TEST_DATA_FOLDER_PATH):
        if with_path:
            for i, filename in enumerate(file_names):
                file_names[i] = os.path.join(TEST_DATA_FOLDER_PATH, filename)
        ret_file_names.extend(file_names)

    return sorted(ret_file_names)


def get_abs_path(filename):
    """
    :returns: The absolute path of the test data file name.
    :raises: :py:exc:`TestFileDoesntExistError` if the filename is not in the test folder.
    """
    abs_path = os.path.abspath(os.path.join(TEST_DATA_FOLDER_PATH, filename))
    if not os.path.exists(abs_path):
        raise TestFileDoesntExistError(
            "Test file '{0}' does not exist under directory '{1}'.".format(filename, TEST_DATA_FOLDER_PATH))
    return abs_path

# TODO add function for searching file names by keyword.
