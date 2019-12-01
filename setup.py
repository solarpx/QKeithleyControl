from setuptools import setup, find_packages

setup(
  name='QKeithleyControl',
  version='1.0',
  description='¨Software Controller for Keithley 2400 sourcemeters',
  license="MIT",
  author='M. Winters',
  url="https://github.com/mwchalmers/QKeithleyControl",
  packages=find_packages(),  #same as name
  install_requires=['visa', 'matplotlib', 'PyQt5'], #external packages as dependencies
)