from setuptools import setup
from codecs import open  # To use a consistent encoding
from os import path


here = path.abspath(path.dirname(__file__))


# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

# Get content from __about__.py
about = {}
with open(path.join(here, 'waterloo', '__about__.py'), 'r', 'utf-8') as f:
    exec(f.read(), about)


setup(
    name='waterloo',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=about['__version__'],

    description=(
        "Tool to convert 'typed docstrings' (e.g. Sphinx 'Napoleon' "
        "format) to PEP-484 Py3 type annotations or Py2 type comments."
    ),
    long_description=long_description,

    url='https://github.com/anentropic/waterloo',

    author='Anentropic',
    author_email='ego@anentropic.com',

    entry_points={
        "console_scripts": [
            "waterloo = waterloo.cli:main",
        ],
    },

    license='MIT',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Text Processing',
    ],
    install_requires=[
        'megaparsy',
        'bowler',
    ],

    packages=[
        'waterloo',
        'waterloo.parsers',
    ],
)
