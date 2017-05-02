#!/usr/bin/env python
import os
import sys

import subprocess

from setuptools import setup, find_packages

CLASSIFIERS = """\
Development Status :: 2 - Pre-Alpha
Intended Audience :: Science/Research
License :: OSI Approved :: Apache Software License
'Programming Language :: Python :: 2',
'Programming Language :: Python :: 2.7',
'Programming Language :: Python :: 3',
'Programming Language :: Python :: 3.3',
'Programming Language :: Python :: 3.4',
'Programming Language :: Python :: 3.5',
Topic :: Scientific/Engineering
Operating System :: Microsoft :: Windows
Operating System :: POSIX
Operating System :: Unix
Operating System :: MacOS
"""

# Use the README as the long description
with open('README.md') as f:
    long_description = f.read()

def is_package(path):
    """
    :param path: Path to check
    :return: true if the path is a package, ie if it has an __init__.py
    """
    return os.path.isfile(os.path.join(path, '__init__.py'))

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


MAJOR = 1
MINOR = 0
MACRO = 0
PRERELEASE = '.a1'
IS_RELEASE = False
VERSION = '%d.%d.%d%s' % (MAJOR, MINOR, MACRO, PRERELEASE)


def get_version_info():
    full_version = VERSION
    if os.path.exists('.git'):
        git_revision = git_version()
    elif os.path.exists('pypore/version.py'):
        # must be a source distribution, use existing version file.
        # load it as a separate module to not load pypore/__init__.py
        import imp

        version = imp.load_source('pypore.version', 'pypore/version.py')
        git_revision = version.git_revision
    else:
        git_revision = "Unknown"

    if not IS_RELEASE:
        # If we are deploying from the Travis CI server, then add a time string to the version,
        # Hopefully it increments better.
        # TODO change this to 'git describe' once we tag a version.
        if 'TRAVIS_PYTHON_VERSION' in os.environ:
            import time
            time_str = time.strftime('%Y%m%d%H%M%S') + '-'
        else:
            time_str = ''
        import time
        full_version += '.dev-' + time_str + git_revision[:7]

    return full_version, git_revision


def write_version_py(filename_pypore='pypore/version.py'):
    """
    Rewrites the pypore/version.py files.
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

    for filename in [filename_pypore]:

        a = open(filename, 'w')
        try:
            a.write(text % {'version': VERSION,
                            'full_version': full_version,
                            'git_revision': git_revision,
                            'is_release': str(IS_RELEASE)})
        finally:
            a.close()


def _get_version_from_py():
    """
    Reads the 'version' from the python file.
    """
    import imp
    module = imp.load_source('pypore.version', 'pypore/version.py')
    return module.version


def setup_package():
    # rewrite the version file every time
    write_version_py()

    metadata = dict(
        name='pypore',
        description='Pythonic Nanopore Translocation Analysis',
        license='MIT',
        long_description=long_description,
        author='Will Parkin',
        author_email='wmparkin@gmail.com',
        url='http://www.github.com/parkin/pypore',
        install_requires=['numpy'],
        # include_dirs=[numpy.get_include()],
        packages=find_packages(),
        test_suite='nose.collector',
        tests_require=['nose', 'scipy'],
        version=_get_version_from_py()
    )

    setup(**metadata)


if __name__ == '__main__':
    setup_package()
