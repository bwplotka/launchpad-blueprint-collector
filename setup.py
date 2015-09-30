import py2exe

from distutils.core import setup
setup(windows=[{"script": "bp_collector.py"}],
      options={"py2exe": {"includes": ["sip"]}},
      requires=["urllib3", "PyQt4"])