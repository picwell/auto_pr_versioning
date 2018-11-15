import subprocess

from setuptools import find_packages, setup

process = subprocess.Popen(['git', 'describe', '--tags', '--abbrev=0'], stdout=subprocess.PIPE)
_VERSION = process.communicate()[0]
_VERSION = _VERSION.strip() if _VERSION else 'v0.0.0'

setup(
    name='auto_pr_versioning',
    packages=find_packages(),
    version=_VERSION,
    description='A tool for automating semantic versioning of Github repositories',
    author='Picwell',
    author_email='dev@picwell.com',
    url='http://www.picwell.com/',
    install_requires=['PyGithub']
)
