from setuptools import setup, find_packages


setup(name='open-source',
      version='1.0',
      author='Nkosana Nikani',
      packages=find_packages(exclude=['tests', 'tests.*']),
      install_requires=[
          'falcon',
          'falcon-cors',
          'gunicorn',
          'sqlalchemy',
          'raven',
          'deepdiff',
          'mysqlclient',
          'reportlab',
          'borb',
          'Jinja2'
      ],
      extras_require={
          'dev': ['flake8'],
      }
      )
