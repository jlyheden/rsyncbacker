from setuptools import setup

setup(
    name="rsyncbacker",
    version="0.0.1",
    packages=['rsyncbacker'],
    scripts=[
        'scripts/rsyncbacker_cmd.py',
        'scripts/freenas_snapshot.py'
    ],
    setup_requires=[
        'nose'
    ],
    install_requires=[
        'pyyaml',
        'requests'
    ],

    # metadata for upload to PyPI
    author="Johan Lyheden",
    author_email="pypi-johan@lyheden.com",
    description="A small piece of python software that manages backups using rsync",
    license="Apache 2.0",
    keywords="backup freenas rsync",
)