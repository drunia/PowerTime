from setuptools import setup

setup(
    name='PowerTime',
    version='1.0.0',
    packages=['ui', 'res', 'devices', 'plugins'],
    url='',
    license='',
    author='drunia',
    author_email='druniax@gmail.com',
    description='Power by time management client',
    install_requires=['PyQt5', 'win32gui', 'serial', 'PySide']
)
