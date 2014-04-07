from functools import wraps
import inspect
import os


def _test_file_manager(directory):
    """
    Decorator. Creates a test filename based on the decorated function's name. Makes sure this file is removed before and after
    the decorated function is called. Calls the decorated function with an extra named parameter filename.

    :param directory: Directory in which to save the file.
    """

    def real_dec(function):
        @wraps(function)
        def wrap(*args, **kwargs):
            arg_spec = inspect.getargspec(function)
            filename = ""
            if 'self' in arg_spec.args:
                filename += args[0].__class__.__name__ + "_"
            filename += function.__name__ + '.h5'

            filename = os.path.join(directory, filename)

            if os.path.exists(filename):
                os.remove(filename)

            function(*args, filename=filename, **kwargs)

            if os.path.exists(filename):
                os.remove(filename)

        return wrap

    return real_dec
