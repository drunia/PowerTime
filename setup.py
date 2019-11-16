from setuptools import setup

setup(
    name='PowerTime',
    version='1.0.0',
    packages=['ui', 'res', 'devices', 'plugins'],
    url='',
    license='LGPL',
    author='drunia',
    author_email='druniax@gmail.com',
    description='Power management util',
    install_requires=['serial', 'PySide', 'pyudev']
)
