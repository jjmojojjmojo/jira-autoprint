from setuptools import setup, find_packages
import os

version = '0.0.1-alpha'

setup(name='autoprint',
      version=version,
      description="Pluggable Automatic Printing Service",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='Josh Johnson',
      author_email='lionface.lemonface@gmail.com',
      url='https://github.com/jjmojojjmojo/jira-autoprint',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['autoprint'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'pycups',
          'reportlab',
          'twisted',
          'colander',
          'deform',
          'jinja2',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      [autoprint.renderers]
      issuecard = autoprint.renderers.issuecard:IssueCardRenderer
      """,
      )
