from setuptools import setup, find_packages

from ulogger import __version__
setup(
    name='micropython-ulogger',
    version=__version__,
    description="Log module customized for micropython.",
    packages=find_packages(),

    url='https://github.com/Li-Lian1069/micropython-ulogger',
    author='M-Jay',
    author_email='m-jay-1376@qq.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
    ],
    keywords='micropython',
)
