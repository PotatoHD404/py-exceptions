from setuptools import setup

setup(
	name='py-exceptions',
	version='1.0.0',
	url='https://github.com/PotatoHD404/py-exceptions',
	description='A simple python exception reporter',
	author='PotatoHD404',
	license='MIT',
	classifiers=[
		'Development Status :: 3 - Alpha',
		'Intended Audience :: Developers',
		'License :: MIT License',
		'Programming Language :: Python :: 3.8',
		'Programming Language :: Python :: 3.9',
	],
	keywords='py-exceptions',
	packages=['pyexceptions'],
	install_requires=[
		'Werkzeug>=2.0.1',
		'Jinja2'
	]
)
