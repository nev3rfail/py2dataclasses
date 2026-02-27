"""Setup script for py2dataclasses - works on Python 2.7+ and Python 3."""
import io
from setuptools import setup

with io.open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='py2dataclasses',
    version='3.14.2',
    description='PEP-557 compatible dataclasses backport for Python 2.7+',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='nev3rfail',
    license='MIT',
    package_dir={'': 'src'},
    packages=['dataclasses'],
    python_requires='>=2.7',
    install_requires=[
        'typing>=3.7; python_version<"3.5"',
        'typing-extensions>=3.7; python_version<"3.8"',
        'dictproxyhack>=1.1; python_version<"3.0"',
        'funcsigs>=1.0; python_version<"3.0"',
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
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries',
    ],
)
