#!/usr/bin/env python
"""
Finds all of the .pyx files and cythonizes them to .c files.
It can be run from the command line by one of the following::

    $ ./tools/cythonize.py [root_dir]
    $ python tools/cythonize.py [root_dir]

Default root_dir: 'src/pypore'

Note that it must be run from the project root's directory.

The script checks a hash database (default 'cythonize.dat') and only Cythonizes
a .pyx file if there are changes to it.

Originally written by Dag Sverre Seljebotn, and copied here from:

https://raw.github.com/dagss/private-scipy-refactor/cythonize/cythonize.py

Note: this script does not check any of the dependent C libraries; it only
operates on the Cython .pyx files.
"""
import hashlib
import os
import sys
import subprocess

HASH_FILE = 'cythonize.dat'
DEFAULT_ROOT = 'src/pypore'


def load_hashes(filename):
    """
    Loads the hashes from the hash file.
    """
    hashes = {}
    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            for line in f:
                filename, inhash, outhash = line.split()
                hashes[filename] = (inhash, outhash)

    return hashes


def sha1_of_file(filename):
    h = hashlib.sha1()
    with open(filename, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()


def get_hash(from_path, to_path):
    from_hash = sha1_of_file(from_path)
    to_hash = sha1_of_file(to_path) if os.path.exists(to_path) else None
    return from_hash, to_hash


def norm_path(path):
    path = path.replace(os.sep, '/')
    if path.startswith('./'):
        path = path[2:]
    return path


def process_pyx(from_file, to_file):
    try:
        from Cython.Compiler.Version import version as cython_version
        from distutils.version import LooseVersion
        if LooseVersion(cython_version) < LooseVersion('0.19'):
            raise Exception('Building SciPy requires Cython >= 0.19. Currently have Cython ' + cython_version)

    except ImportError:
        pass

    flags = ['--fast-fail']
    if to_file.endswith('.cxx'):
        flags += ['--cplus']

    try:
        try:
            r = subprocess.call(['cython'] + flags + ["-o", to_file, from_file])
            if r != 0:
                raise Exception('Cython failed')
        except OSError:
            # There are ways of installing Cython that don't result in a cython
            # executable on the path, see gh-2397.
            r = subprocess.call([sys.executable, '-c',
                                 'import sys; from Cython.Compiler.Main import '
                                 'setuptools_main as main; sys.exit(main())'] + flags +
                                 ["-o", to_file, from_file])
            if r != 0:
                raise Exception('Cython failed')
    except OSError:
        raise OSError('Cython needs to be installed')


def process(path, from_file, to_file, hash_db):
    full_from_path = os.path.join(path, from_file)
    full_to_path = os.path.join(path, to_file)
    current_hash = get_hash(full_from_path, full_to_path)
    if current_hash == hash_db.get(norm_path(full_from_path), None):
        print '%s has not changed' % full_from_path
        return

    orig_cwd = os.getcwd()
    try:
        os.chdir(path)
        print 'Processing %s' % full_from_path
        process_pyx(from_file, to_file)
    finally:
        os.chdir(orig_cwd)
    # changed target file, recompute hash
    current_hash = get_hash(full_from_path, full_to_path)
    # store hash in db
    hash_db[norm_path(full_from_path)] = current_hash


def save_hashes(hash_db, filename):
    with open(filename, 'w') as f:
        for key, value in sorted(hash_db.items()):
            f.write("%s %s %s\n" % (key, value[0], value[1]))


def find_process_files(root_dir):
    """
    Finds all of the Cython files (with .pyx extensions), and
    compiles them.
    """
    hash_db = load_hashes(HASH_FILE)
    for cur_dir, dirs, files in os.walk(root_dir):
        for filename in files:
            if filename.endswith('.pyx'):
                fromext = '.pyx'
                toext = '.c'
                fromfile = filename
                tofile = filename[:-len(fromext)] + toext
                process(cur_dir, fromfile, tofile, hash_db)
                save_hashes(hash_db, HASH_FILE)


def main():
    try:
        root_dir = sys.argv[1]
    except IndexError:
        root_dir = DEFAULT_ROOT
    find_process_files(root_dir)

if __name__ == '__main__':
    main()