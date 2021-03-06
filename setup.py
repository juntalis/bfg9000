import os
import platform
import re
import subprocess
import sys
from setuptools import setup, find_packages, Command

from bfg9000.app_version import version

root_dir = os.path.abspath(os.path.dirname(__file__))


class DocServe(Command):
    description = 'serve the documentation locally'
    user_options = [
        ('dev-addr=', None, 'address to host the documentation on'),
    ]

    def initialize_options(self):
        self.dev_addr = '0.0.0.0:8000'

    def finalize_options(self):
        pass

    def run(self):
        subprocess.check_call([
            'mkdocs', 'serve', '--dev-addr=' + self.dev_addr
        ])


class DocDeploy(Command):
    description = 'push the documentation to GitHub'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        subprocess.check_call(['mkdocs', 'gh-deploy', '--clean'])


class Coverage(Command):
    description = 'run tests with code coverage'
    user_options = [
        ('test-suite=', 's',
         "test suite to run (e.g. 'some_module.test_suite')"),
    ]

    def initialize_options(self):
        self.test_suite = None

    def finalize_options(self):
        pass

    def run(self):
        env = dict(os.environ)
        pythonpath = os.path.join(root_dir, 'test', 'scripts')
        if env.get('PYTHONPATH'):
            pythonpath += os.pathsep + env['PYTHONPATH']
        env.update({
            'PYTHONPATH': pythonpath,
            'COVERAGE_FILE': os.path.join(root_dir, '.coverage'),
            'COVERAGE_PROCESS_START': os.path.join(root_dir, '.coveragerc'),
        })

        subprocess.check_call(['coverage', 'erase'])
        subprocess.check_call(
            ['coverage', 'run', 'setup.py', 'test'] +
            (['-q'] if self.verbose == 0 else []) +
            (['-s', self.test_suite] if self.test_suite else []),
            env=env
        )
        subprocess.check_call(['coverage', 'combine'])


custom_cmds = {
    'doc_serve': DocServe,
    'doc_deploy': DocDeploy,
    'coverage': Coverage,
}

try:
    from flake8.main.setuptools_command import Flake8

    class LintCommand(Flake8):
        def distribution_files(self):
            return ['setup.py', 'bfg9000', 'examples', 'test']

    custom_cmds['lint'] = LintCommand
except ImportError:
    pass

more_scripts = []
more_requires = []

if os.getenv('NO_DOPPEL') not in ['1', 'true']:
    more_requires.append('doppel >= 0.2')

if sys.version_info < (3, 4):
    more_requires.append('enum34')

platform_name = platform.system()
if platform_name == 'Windows':
    more_scripts.append('bfg9000-setenv=bfg9000.setenv:main')
elif platform_name == 'Linux':
    if os.getenv('NO_PATCHELF') not in ['1', 'true']:
        more_requires.append('patchelf-wrapper')

with open(os.path.join(root_dir, 'README.md'), 'r') as f:
    # Read from the file and strip out the badges.
    long_desc = re.sub(r'(^# bfg9000.*)\n\n(.+\n)*', r'\1', f.read())

try:
    import pypandoc
    long_desc = pypandoc.convert(long_desc, 'rst', format='md')
except ImportError:
    pass

setup(
    name='bfg9000',
    version=version,

    description='A cross-platform build file generator',
    long_description=long_desc,
    keywords='build file generator',
    url='https://jimporter.github.io/bfg9000/',

    author='Jim Porter',
    author_email='porterj@alum.rit.edu',
    license='BSD',

    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',

        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    packages=find_packages(exclude=['test', 'test.*']),

    install_requires=(
        ['colorama', 'packaging', 'setuptools', 'six'] +
        more_requires
    ),
    extras_require={
        'dev': ['coverage', 'flake8 >= 3.0', 'mkdocs', 'mkdocs-bootswatch',
                'pypandoc'],
        'test': ['coverage', 'flake8 >= 3.0'],
        'msbuild': ['lxml'],
    },

    entry_points={
        'console_scripts': [
            'bfg9000=bfg9000.driver:main',
            '9k=bfg9000.driver:simple_main',
            'bfg9000-depfixer=bfg9000.depfixer:main',
            'bfg9000-jvmoutput=bfg9000.jvmoutput:main',
        ] + more_scripts,
        'bfg9000.backends': [
            'make=bfg9000.backends.make.writer',
            'ninja=bfg9000.backends.ninja.writer',
            'msbuild=bfg9000.backends.msbuild.writer [msbuild]',
        ],
        'bfg9000.platforms': [
            'cygwin=bfg9000.platforms.windows:CygwinPlatform',
            'darwin=bfg9000.platforms.posix:DarwinPlatform',
            'linux=bfg9000.platforms.posix:LinuxPlatform',
            'posix=bfg9000.platforms.posix:PosixPlatform',
            'windows=bfg9000.platforms.windows:WindowsPlatform',
        ],
    },

    test_suite='test',
    cmdclass=custom_cmds,
)
