
from pyporegui.version import version as __version__


def start():
    """
    Starts PyporeGui.

    >>> import pyporegui
    >>> pyporegui.start()
    """
    from pyporegui.gui import start as _start
    _start()
