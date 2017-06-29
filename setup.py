"""
Constant-time string comparison
-------------------------------

Sometimes you need to test strings for equality with an algorithm whose timing depends
only on the length of the strings, and not on the contents of the strings themselves. If
one of those strings is of constant width -- an
`HMAC <http://en.wikipedia.org/wiki/HMAC>`_, for example -- then it becomes a constant-time
operation. This can be used to prevent some `timing side-channel
attacks <http://en.wikipedia.org/wiki/Timing_attack>`_, such as `the critical vulnerability
found in KeyCzar back in 2009 <http://codahale.com/a-lesson-in-timing-attacks/>`_.

This module offers a single function, ``equals(x, y)``, which takes two strings ``x`` and
``y`` and returns ``True`` if they are equal, and ``False`` if they are not. The time
this function takes does not depend on what specific bytes are in these strings. Unicode
strings are encoded as UTF-8 before being compared; it is recommended that you only use
this on byte strings (``str`` in Python 2, ``bytes`` in Python 3).

This works with Python 2 and 3, and PyPy. The license is Apache 2.0.
"""
import sys

try:
  from setuptools import setup, Extension
except ImportError:
  from distutils.core import setup
  from distutils.extension import Extension

from distutils.command.build_ext import build_ext
from distutils.errors import CCompilerError, DistutilsExecError, \
  DistutilsPlatformError


class BuildFailed(Exception):
  pass

class ve_build_ext(build_ext):
  """This class allows C extension building to fail."""
  ext_errors = (CCompilerError, DistutilsExecError, DistutilsPlatformError)
  if sys.platform == 'win32' and sys.version_info < (2, 7):
    # 2.6's distutils.msvc9compiler can raise an IOError when failing to
    # find the compiler
    # It can also raise ValueError http://bugs.python.org/issue7511
    ext_errors += (IOError, ValueError)

  def run(self):
    try:
      build_ext.run(self)
    except DistutilsPlatformError:
      raise BuildFailed()

  def build_extension(self, ext):
    try:
      build_ext.build_extension(self, ext)
    except self.ext_errors:
      raise BuildFailed()
    except ValueError:
      # this can happen on Windows 64 bit, see Python issue 7511
      if "'path'" in str(sys.exc_info()[1]): # works with Python 2 and 3
        raise BuildFailed()
      raise


common = dict(
    name = 'streql',
    version = '3.0.2',
    description = 'Constant-time string comparison',
    long_description = __doc__,
    author = 'Peter Scott',
    author_email = 'peter@cueup.com',
    license = 'Apache',
    url = 'https://github.com/PeterScott/streql',
    test_suite = 'tests',
    zip_safe = False,
    classifiers = [
      'Development Status :: 5 - Production/Stable',
      'License :: OSI Approved :: Apache Software License',
      'Operating System :: OS Independent',
      'Programming Language :: Python',
      'Programming Language :: Python :: 2',
      'Programming Language :: Python :: 3',
      'Programming Language :: Python :: Implementation :: CPython',
      'Programming Language :: Python :: Implementation :: PyPy',
      'Topic :: Security',
      'Topic :: Security :: Cryptography',
    ],
)

def setup_c_extension():
  setup(ext_modules=[Extension("streql", ["streql.c"])],
        cmdclass={'build_ext': ve_build_ext},
        **common)

def setup_pure_python():
  setup(py_modules=['streql'], package_dir={'': 'pypy'}, **common)


is_pypy = hasattr(sys, 'pypy_version_info')

if is_pypy:
  setup_pure_python()
else:
  try:
    setup_c_extension()
  except BuildFailed:
    # install the pure-Python version,
    # while printing useful output so the user knows what happened
    def echo(msg=''):
      sys.stdout.write(msg + '\n')

    line = '=' * 74
    build_ext_warning = 'WARNING: The C extensions could not be ' \
                        'compiled; speedups are not enabled.'

    echo(line)
    echo(build_ext_warning)
    echo('Failure information, if any, is above.')
    echo('Retrying the build without the C extension now.')
    echo()

    setup_pure_python()

    echo(line)
    echo(build_ext_warning)
    echo('Plain-Python installation succeeded.')
    echo(line)
