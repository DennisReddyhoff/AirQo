from distutils.core import setup
setup(
  name = 'get_dataframe',
  packages = ['get_dataframe'], # this must be the same as the name above
  version = '1.0',
  description = 'Download and cache data from AirQo sensors',
  author = 'Dennis Reddyhoff',
  author_email = 'd.reddyhoff@sheffield.ac.uk',
  url = 'https://github.com/DennisReddyhoff/AirQo.git',
  keywords = ['airqo'],
  classifiers = [],
  install_requires=['requests', 'pandas'],
)
