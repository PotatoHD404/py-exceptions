from setuptools import setup
import pathlib

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

setup(
    name='py-exceptions',
    version='1.0.0',
    url='https://github.com/PotatoHD404/py-exceptions',
    description='A simple python exception reporter',
    author='PotatoHD404',
    include_package_data=True,
    license='MIT',
    long_description=README,
    long_description_content_type="text/markdown",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    keywords='py-exceptions',
    packages=['pyexceptions'],
    install_requires=[
        'Werkzeug>=2.0.1',
        'Jinja2'
    ]
)
