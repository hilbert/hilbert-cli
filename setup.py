#!/usr/bin/env python
# -*- coding: utf-8 -*-

# from distutils.core import setup # no support for install_requires!
from setuptools import setup # supports install_requires!

#from pip.req import parse_requirements
# See: https://stackoverflow.com/a/16624700
# Fix: https://stackoverflow.com/a/25193001
def parse_requirements(filename, session='hack'):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")] # .req : line ?

install_reqs = parse_requirements('requirements.txt', session='hack')
tests_reqs = parse_requirements('requirements-dev.txt', session='hack')

setup(name='hilbert_config',
      version='0.4.0',
      description='Hilbert Configuration tool (server part)',
      url='https://github.com/hilbert/hilbert-cli',
      author='Oleksandr Motsak',
      author_email='http://goo.gl/mcpzY',
      packages=['hilbert_config'],
      package_dir={'hilbert_config': 'hilbert_config'},  # package_data={'...': ['data/*.dat']},
      # py_modules=['tools/hilbert.py'],
      scripts=['tools/hilbert', 'tools/hilbert.py', 'server/list_stations.sh', 'server/stop_station.sh', 'server/start_station.sh', 'server/appchange_station.sh', 'server/list_applications.sh', 'server/list_profiles.sh'],
      license='Apache License 2.0',
      classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Topic :: Utilities',
        'Programming Language :: Unix Shell',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
      ],
      platforms=[''],  # data_files=[('config/templates', ['docker-compose.yml'])],
      install_requires=[str(ir) for ir in install_reqs],
      tests_require=[str(ir) for ir in tests_reqs]
      )
# glob.glob(os.path.join('mydir', 'subdir', '*.html'))
# os.listdir(os.path.join('mydir', 'subdir'))

