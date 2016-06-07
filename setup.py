import setuptools
import os

import inotify

APP_PATH = os.path.dirname(inotify.__file__)

with open(os.path.join(APP_PATH, 'resources', 'README.rst')) as f:
      _LONG_DESCRIPTION = f.read()

with open(os.path.join(APP_PATH, 'resources', 'requirements.txt')) as f:
      _INSTALL_REQUIRES = list(map(lambda s: s.strip(), f.readlines()))

_DESCRIPTION = \
    "An adapter to Linux kernel support for inotify directory-watching."

setuptools.setup(
    name='inotify',
    version=inotify.__version__,
    description=_DESCRIPTION,
    long_description=_LONG_DESCRIPTION,
    classifiers=[
    ],
    keywords='inotify',
    author='Dustin Oprea',
    author_email='myselfasunder@gmail.com',
    url='https://github.com/dsoprea/PyInotify',
    license='GPL 2',
    packages=setuptools.find_packages(exclude=['dev']),
    include_package_data=True,
    zip_safe=False,
    install_requires=_INSTALL_REQUIRES,
    package_data={
        'inotify': [
            'resources/README.rst',
            'resources/requirements.txt',
        ]
    }
)
