from setuptools import setup
from codecs import open  # To use a consistent encoding
from os import path


here = path.abspath(path.dirname(__file__))


# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
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
        "Tool to convert 'typed docstrings' (i.e. 'Google-style', Sphinx "
        "'Napoleon' format) to PEP-484 Py2 type comments."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",

    url='https://github.com/anentropic/python-waterloo',

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
    python_requires='~=3.7',
    install_requires=[
        'megaparsy>=0.1.4,<0.2.0',
        # 'bowler @ https://github.com/anentropic/Bowler/tarball/0.8.0-post2#egg=bowler-0.8.0-post2',
        'prompt-toolkit>=3.0.0,<3.1.0',
        'toml>=0.10.0,<0.11.0',
        'regex>=2020.2.20',
        'pydantic>=1.4,<1.5',
        'typing-extensions>=3.7,<3.8',
        'parso>=0.6,<0.7',
        'Inject>=4.1,<4.2',
        # Bowler deps:
        'attrs',
        'click',
        'fissix',
        'moreorless>=0.2.0',
        'volatile',
    ],

    packages=[
        'bowler',
        'waterloo',
        'waterloo.conf',
        'waterloo.parsers',
        'waterloo.refactor',
    ],

    # https://mypy.readthedocs.io/en/latest/installed_packages.html#making-pep-561-compatible-packages
    package_data={
        'waterloo': ['py.typed'],
    },
    # zip_safe=False,
)
