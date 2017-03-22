from setuptools import setup
from setuptools import find_packages

setup(name='borg-summon',
    version='0.1',
    description='A work-in-progress wrapper for automating BorgBackup use',
    url='https://github.com/grensjo/borg-summon',
    author='Anton Grensjö',
    author_email='anton@grensjo.se',
    license='MIT',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    install_requires=[
        'toml',
        'click',
        'sh',
        ],
    setup_requires=[
        'pytest-runner',
        ],
    tests_require=[
        'pytest',
        'pytest-cov',
        ],
    entry_points={
        'console_scripts': ['borg-summon=borg_summon.command_line:main']
    },
    zip_safe=True)
