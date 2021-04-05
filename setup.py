from setuptools import setup, find_packages
import os
import pathlib

setup(
    name='humidifier-controller',
    version='0.5a5',
    author='Sabin Serban',
    description='Serial server and client to log data from humidity sensors',
    packages=find_packages(include=['humidifier-controller', 'humidifier-controller.*']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Pyro5'
    ],
    scripts=['bin/humidifier-controller-console']
)

# create data directory if it does not already exist
# (directory already set in systemd service)
user = os.path.basename(pathlib.Path.home())
working_dir = os.path.join(pathlib.Path.home(),  '.local/share/humidifier')
try:
    os.makedirs(working_dir)
except OSError:
    pass

# print('Please create the file "humidifier-controller.service" in your sytemd folder')
# print('located in "/lib/systemd/system/" on Debian systems, and copy the following code:')