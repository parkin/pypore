"""
Not a very useful class, basically just a list with less methods.
@author: `@parkin`_
"""


class _ThreadManager(object):
    def __init__(self, *args, **kargs):
        """
        """
        super(_ThreadManager, self).__init__()
        self.thread_pool = []

    def add_thread(self, thread):
        self.thread_pool.append(thread)

    def clean_threads(self):
        """
        Cancels all of the currently running threads.
        """
        for w in self.thread_pool:
            w.cancel()
            #             w.wait()
            self.thread_pool.remove(w)

    def remove_thread(self, thread):
        """
        Removes the thread from the threadPool.
        """
        self.thread_pool.remove(thread)


