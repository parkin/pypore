#!/usr/bin/env python
import os
import sys

import numpy
import subprocess

CLASSIFIERS = """\
Development Status :: 2 - Pre-Alpha
Intended Audience :: Science/Research
License :: OSI Approved :: Apache Software License
Programming Language :: Python
Programming Language :: Python :: 2.7
Programming Language :: Cython
Topic :: Scientific/Engineering
Operating System :: Microsoft :: Windows
Operating System :: POSIX
Operating System :: Unix
Operating System :: MacOS
"""

with open('README.rst') as f:
    long_description = f.read()


def is_package(path):
    return os.path.isfile(os.path.join(path, '__init__.py'))


def find_extensions(root):
    """
    Find all the .c files under root directory.
    yields Extension's

    Only yields C files that are in a python package (aka in dir with __init__.py).

    :param string root: root directory to search.
    :returns: Yields a distutils.extension.Extension every time it finds a C file.
    """
    from distutils.extension import Extension

    for path, directories, files in os.walk(root):
        if is_package(path):
            for filename in files:
                if filename.endswith('.c'):
                    full_name = os.path.join(path, filename)
                    module_name = filename[:-len('.c')]
                    full_module_name = get_package_name_from_path(path) + '.' + module_name
                    yield Extension(full_module_name, sources=[full_name], include_dirs=[numpy.get_include()])


def get_package_name_from_path(package_path):
    """
    :param str package_path: path of a package
    :returns: string -- full package name, including super packages\
                for a give package_path that is already a package.
    """
    if not is_package(package_path):
        raise ValueError('parameter not a package')
    up_path, end = os.path.split(package_path)
    ret = end
    while end != '' and is_package(up_path):
        up_path, end = os.path.split(up_path)
        ret = end + '.' + ret
    return ret


def find_packages(root):
    """
    Find all the packages under root directory.

    :param string root: root directory to search
    """
    for path, directories, files in os.walk(root):
        if is_package(path):
            yield get_package_name_from_path(path)


def git_version():
    """
    :returns: the git revision as a string.
    """

    def _minimal_ext_cmd(cmd):
        # construct minimal environment
        env = {}
        for k in ['SYSTEMROOT', 'PATH']:
            v = os.environ.get(k)
            if v is not None:
                env[k] = v
        # LANGUAGE is used on Win32
        env['LANGUAGE'] = 'C'
        env['LANG'] = 'C'
        env['LC_ALL'] = 'C'
        out = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=env).communicate()[0]
        return out

    try:
        out = _minimal_ext_cmd(['git', 'rev-parse', 'HEAD'])
        git_revision = out.strip().decode('ascii')
    except OSError:
        git_revision = "Unknown"

    return git_revision


MAJOR = 0
MINOR = 0
MACRO = 6
IS_RELEASE = False
VERSION = '%d.%d.%d' % (MAJOR, MINOR, MACRO)


def get_version_info():
    full_version = VERSION
    if os.path.exists('.git'):
        git_revision = git_version()
    elif os.path.exists('src/pypore/version.py'):
        # must be a source distribution, use existing version file.
        # load it as a separate module to not load pypore/__init__.py
        import imp

        version = imp.load_source('pypore.version', 'src/pypore/version.py')
        git_revision = version.git_revision
    else:
        git_revision = "Unknown"

    if not IS_RELEASE:
        # If we are deploying from the Travis CI server, then add a time string to the version,
        # Hopefully it increments better.
        # TODO change this to 'git describe' once we tag a version.
        if 'TRAVIS_PYTHON_VERSION' in os.environ:
            import time
            time_str = time.strftime('%Y%m%d%H%M%S')
        else:
            time_str = ''

        full_version += '.dev' + time_str

    return full_version, git_revision


def write_version_py(filename_pypore='src/pypore/version.py', filename_pyporegui='src/pyporegui/version.py'):
    """
    Rewrites the src/pypore/version.py and src/pyporegui/version.py files.
    """
    text = """
# THIS FILE IS GENERATED FROM SETUP.PY
short_version = '%(version)s'
version = '%(version)s'
full_version = '%(full_version)s'
git_revision = '%(git_revision)s'
release = %(is_release)s

if not release:
    version = full_version
"""
    full_version, git_revision = get_version_info()

    for filename in (filename_pypore, filename_pyporegui):

        a = open(filename, 'w')
        try:
            a.write(text % {'version': VERSION,
                            'full_version': full_version,
                            'git_revision': git_revision,
                            'is_release': str(IS_RELEASE)})
        finally:
            a.close()


def generate_cython():
    """
    Calls tools/cythonize.py to Cythonize .pyx files to C files.
    """
    cwd = os.path.abspath(os.path.dirname(__file__))
    print("Cythonizing sources")
    p = subprocess.call([sys.executable,
                         os.path.join(cwd, 'tools', 'cythonize.py'),
                         'src/pypore'],
                        cwd=cwd)
    if p != 0:
        raise RuntimeError("Running cythonize failed!")


def _get_version_from_py():
    """
    Reads the 'version' from the python file.
    """
    import imp
    module = imp.load_source('pypore.version', 'src/pypore/version.py')
    return module.version


def setup_package():
    # rewrite the version file every time
    write_version_py()

    metadata = dict(
        name='pypore',
        description='Pythonic/Cythonic Nanopore Translocation Analysis',
        long_description=long_description,
        scripts=['bin/filterfiles.py', 'bin/pypore_batch_csv.py'],
        author='Will Parkin',
        author_email='wmparkin@gmail.com',
        url='http://parkin.github.io/pypore/',
        requires=['numpy', 'scipy', 'tables', 'PySide', 'pyqtgraph'],
        include_dirs=[numpy.get_include()],
        package_dir={'': 'src'},
        test_suite='nose.collector',
        tests_require=['nose']
    )

    if len(sys.argv) >= 2 and ('--help' in sys.argv[1:] or
                                       sys.argv[1] in ('--help-commands', 'egg_info', '--version',
                                                       'clean')):
        # for these actions, a full build is not required.
        fullversion, git_revision = get_version_info()
        metadata['version'] = fullversion
    else:
        if len(sys.argv) >= 2 and sys.argv[1] == 'bdist_wheel':
            # bdist_wheel needs setuptools
            import setuptools

        cwd = os.path.abspath(os.path.dirname(__file__))
        if not os.path.exists(os.path.join(cwd, 'PKG-INFO')):
            # Generate Cython sources, unless building from source release
            generate_cython()

        # a pypore.version should exist
        metadata['version'] = _get_version_from_py()

    try:
        from setuptools import setup
    except ImportError:
        from distutils.core import setup

    packages = list(find_packages('src'))
    metadata['packages'] = packages

    ext_modules = list(find_extensions('src'))
    metadata['ext_modules'] = ext_modules

    setup(**metadata)


if __name__ == '__main__':
    setup_package()
