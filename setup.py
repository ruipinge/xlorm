from setuptools import setup

from xlorm.info import __VERSION__


setup(
    name='xlorm',
    version=__VERSION__,
    author='Rui Pinge',
    author_email='rui@pinge.org',
    url='https://ruipinge.github.io/xlorm',
    packages=['xlorm'],
    description=(
        'Library for developers to extract data from '
        'Microsoft Excel (tm) .xls spreadsheet files '
        'using an ORM approach'
    ),
    long_description=open('README.md').read(),
    license='BSD',
    keywords=['xls', 'xlsx', 'excel', 'spreadsheet', 'orm'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Operating System :: OS Independent',
        'Topic :: Database',
        'Topic :: Office/Business',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*",
    install_requires=[
        'xlrd == 1.2.0'  # IMPORTANT: any update needs to be reflected in `tox.ini`
    ]
)
