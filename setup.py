from setuptools import setup, find_packages

setup(
    name="rsyncbacker",
    version="0.0.1",
    packages=find_packages(),
    scripts=['scripts/rsyncbacker.py'],
    install_requires=[
        'pyyaml'
    ],

    # metadata for upload to PyPI
    author="Johan Lyheden",
    author_email="pypi-johan@lyheden.com",
    description="A small piece of python software that manages backups using rsync",
    license="Apache 2.0",
    keywords="backup freenas rsync",
)