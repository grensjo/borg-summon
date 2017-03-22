from setuptools import setup

setup(name='borg-summon',
    version='0.1',
    description='A work-in-progress wrapper for automating BorgBackup use',
    url='https://github.com/grensjo/borg-summon',
    author='Anton Grensjö',
    author_email='anton@grensjo.se',
    license='MIT',
    packages=['borg_summon'],
    install_requires=[
        'toml',
        'click',
        'sh',
        ],
    entry_points={
        'console_scripts': ['borg-summon=borg_summon.command_line:main']
    },
    zip_safe=True)
