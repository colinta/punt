import os
from setuptools import setup
from setuptools import find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
        name="punt",
        version="v1.8.2",
        author="Colin Thomas-Arnold",
        author_email="colinta@gmail",
        url="https://github.com/colinta/punt",
        install_requires=['docopt', 'watchdog'],

        entry_points={
            'console_scripts': [
                'punt = punt:run'
            ]
        },

        description="A straightforward python static site generator.",
        long_description=read("README.rst"),

        packages=find_packages(),
        keywords="terminal command shell",
        platforms="any",
        license="BSD",
        classifiers=[
            "Programming Language :: Python",
            "Development Status :: 4 - Beta",
            'Environment :: Console',
            "License :: OSI Approved :: BSD License",
            "Operating System :: OS Independent",

            'Intended Audience :: End Users/Desktop',
            'Intended Audience :: Developers',
            'Intended Audience :: System Administrators',

            'Topic :: Software Development',
        ],
    )
