import setuptools

with open('README.rst') as f:
      long_description = f.read()

with open('requirements.txt') as f:
      install_requires = map(lambda s: s.strip(), f)

setuptools.setup(
      name='inotify',
      version='0.2.0',
      description="An adapter to Linux kernel inotify directory-watching.",
      long_description=long_description,
      classifiers=[],
      keywords='inotify',
      author='Dustin Oprea',
      author_email='myselfasunder@gmail.com',
      url='',
      license='GPL 2',
      packages=['inotify'],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
)
