# -*- coding: utf-8 -*-

"""Setup script for py2dataclasses - works on Python 2.7+ and Python 3."""
from __future__ import print_function

import io
from setuptools import setup, find_packages
# Read the README
with io.open('README.md', encoding='utf-8') as f:
    long_description = f.read()

def version_scheme(version):
    if not version.distance:
        return version.format_with("{tag}")
    return version.format_with("{tag}+{distance}.{node}")

setup(
    name='py2dataclasses',
    description='PEP-557 compatible dataclasses backport for Python 2.7+',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='nev3rfail',
    license='MIT',
    readme="README.md",
    license_files=["LICENSE"],
    license_file="LICENSE",
    #metadata={"":{}},
    url='https://github.com/nev3rfail/py2dataclasses',
    package_dir={'': 'src'},
    py_modules=['dataclasses', 'py2dataclasses'],
    packages=find_packages('src'),
    python_requires='>=2.7',
    use_scm_version={
        "root": ".",
        "relative_to": __file__,
        "version_scheme": version_scheme,
        "local_scheme": "no-local-version",
    },
    setup_requires=["setuptools_scm"],
    install_requires=[
        'typing>=3.7; python_version<"3.5"',
        'unittest-xml-reporting>=1.17.0; python_version<"3.5"',
        'typing-extensions>=3.7; python_version<"3.8"',
        'dictproxyhack>=1.1; python_version<"3.0"',
        'funcsigs>=1.0; python_version<"3.0"',
        'six>=1.17',
        'unittest-xml-reporting>=4.0.0; python_version>"3.5"',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Topic :: Software Development :: Libraries',
    ],
)
