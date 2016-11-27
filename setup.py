from distutils.core import setup

setup(name='Hilbert',
      version='0.2.2',
      description='Hilbert tool (server part)',
      url='https://github.com/hilbert/hilbert-cli',
      author='Oleksandr Motsak',
      author_email='http://goo.gl/mcpzY',
      packages=['config'],
      package_dir={'config': 'config'},  # package_data={'...': ['data/*.dat']},
      # py_modules=['tools/hilbert.py'],
      scripts=['tools/hilbert', 'tools/hilbert.py'],
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
