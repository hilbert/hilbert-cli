from distutils.core import setup

setup(name='hilbert_config',
      version='0.3.0',
      description='Hilbert Configuration tool (server part)',
      url='https://github.com/hilbert/hilbert-cli',
      author='Oleksandr Motsak',
      author_email='http://goo.gl/mcpzY',
      packages=['hilbert_config'],
      package_dir={'hilbert_config': 'hilbert_config'},  # package_data={'...': ['data/*.dat']},
      # py_modules=['tools/hilbert.py'],
      scripts=['tools/hilbert', 'tools/hilbert.py', 'server/list_stations.sh', 'server/stop_station.sh', 'server/start_station.sh', 'server/appchange_station.sh'],
      license='',
      classifiers=[''],
      platforms=[''],  # data_files=[('config/templates', ['docker-compose.yml'])],
      install_requires=[
          'dill>=0.2.5',
          'semantic_version>=2.6.0',
          'argparse>=1.4.0',
          'argcomplete>=1.6.0',
          'ruamel.yaml>=0.12.15',
      ],
      extras_require={
          ':python_version == "2.7"': [
              'logging',  # TODO: check whether this is really required!?!
          ],
      },
      )  # TODO: add testing!?
# glob.glob(os.path.join('mydir', 'subdir', '*.html'))
# os.listdir(os.path.join('mydir', 'subdir'))

