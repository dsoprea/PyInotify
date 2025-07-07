import setuptools
import os

with open(os.path.join('inotify', 'resources', 'README.rst')) as f:
    _LONG_DESCRIPTION = f.read()

with open(os.path.join('inotify', 'resources', 'requirements.txt')) as f:
    _INSTALL_REQUIRES = list(map(lambda s: s.strip(), f.readlines()))

_DESCRIPTION = \
    "An adapter to Linux kernel support for inotify directory-watching."

setuptools.setup(
    name='inotify',
    version='0.2.11',
    description=_DESCRIPTION,
    long_description=_LONG_DESCRIPTION,
    classifiers=[
    ],
    keywords='inotify',
    author='Dustin Oprea',
    author_email='myselfasunder@gmail.com',
    url='https://github.com/dsoprea/PyInotify',
    license='GPL 2',
    packages=setuptools.find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=_INSTALL_REQUIRES,
    package_data={
        'inotify': [
            'resources/README.rst',
            'resources/requirements.txt',
        ]
    },
)
