from setuptools import setup

setup(
    name='nagios_result_bridge',
    version='0.1',
    description='Pass passive service check results received via TCP to Nagios external command socket if the hostname resolves to the senders address',
    author='Jan-Philipp Litza (PLUTEX)',
    author_email='jpl@plutex.de',
    license='BSD-2',
    py_modules=['nagios_result_bridge'],
    scripts=['bin/nagios_result_bridge'],
    test_suite='test_all',
)
