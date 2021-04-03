from setuptools import setup, find_packages

setup(
    name='humidifier-controller',
    version='0.4a1',
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