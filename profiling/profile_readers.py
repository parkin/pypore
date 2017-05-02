import cProfile

from pypore.i_o.chimera_reader import ChimeraReader
from pypore.i_o.heka_reader import HekaReader
import pypore.sampledata.testing_files as tf


def _reader_tasks(reader):
    for _ in xrange(1000):
        data = reader[:]
        data = reader[::-1]
        data = reader[100]
        data = reader[::-2]
        data = reader[::3]


def profile_chimera():
    filename = tf.get_abs_path('spheres_20140114_154938_beginning.log')
    reader = ChimeraReader(filename)
    _reader_tasks(reader)
    reader.close()


def profile_heka():
    filename = tf.get_abs_path('heka_1.5s_mean5.32p_std2.76p.hkd')
    reader = HekaReader(filename)
    _reader_tasks(reader)
    reader.close()

if __name__ == '__main__':
    print("Profiling ChimeraReader")
    cProfile.run('profile_chimera()', sort='cumtime')

    print("Profiling HekaReader")
    cProfile.run('profile_heka()', sort='cumtime')
